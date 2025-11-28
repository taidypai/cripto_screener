-- executive_script.lua

-- PRICES:GLDRUBF/ЦЕНА; IMOEXF/ЦЕНА
-- DEAL:ticker/operation/QUANTITY
is_run = true

function main()
    local price_file = "C:/QUIK_DATA/price.txt"
    local order_file = "C:/QUIK_DATA/order.txt"

    -- Коды инструментов для мониторинга цен
    local instruments = {
        {class = "SPBFUT", ticker = "GLDRUBF", code = "GLDRUBF"},
        {class = "SPBFUT", ticker = "IMOEXF", code = "IMOEXF"}
    }

    while is_run do
        -- ЗАПИСЬ ЦЕН В price.txt
        local price_strings = {}
        for i, instr in ipairs(instruments) do
            local price_data = getParamEx(instr.class, instr.ticker, "LAST")
            if price_data and price_data.param_value and price_data.param_value ~= "" then
                table.insert(price_strings, instr.code .. ":" .. price_data.param_value)
            end
        end

        local new_price_line = table.concat(price_strings, "; ")

        local price_file_write = io.open(price_file, "w")
        if price_file_write then
            price_file_write:write(new_price_line .. "\n")
            price_file_write:close()
        end

        -- ЧТЕНИЕ И ВЫПОЛНЕНИЕ СДЕЛОК ИЗ order.txt
        local order_file_read = io.open(order_file, "r")
        if order_file_read then
            local lines = {}
            local deal_lines = {}

            -- Читаем все строки и ищем DEAL
            for line in order_file_read:lines() do
                table.insert(lines, line)
                if string.sub(line, 1, 5) == "DEAL:" then
                    table.insert(deal_lines, line)
                end
            end
            order_file_read:close()

            -- Если есть сделки - обрабатываем их
            if #deal_lines > 0 then
                local updated_lines = {}

                for i, line in ipairs(lines) do
                    if string.sub(line, 1, 5) == "DEAL:" then
                        -- Выполняем сделку и НЕ добавляем обратно
                        local deal_data = string.sub(line, 6)
                        local ticker, operation, quantity = string.match(deal_data, "(.+)/(.)/(%d+)")

                        if ticker and operation and quantity then
                            ticker = string.gsub(ticker, "%s+", "")
                            operation = string.gsub(operation, "%s+", "")

                            local transaction = {
                                ["ACTION"] = "NEW_ORDER",
                                ["CLASSCODE"] = "SPBFUT",
                                ["SECCODE"] = ticker,
                                ["OPERATION"] = operation,
                                ["QUANTITY"] = quantity,
                                ["PRICE"] = "0",
                                ["ACCOUNT"] = "L01+00000F00",
                                ["TYPE"] = "M",
                                ["CLIENT_CODE"] = "QLUA_MKT",
                                ["TRANS_ID"] = tostring(os.time() + i)
                            }

                            local result = sendTransaction(transaction)

                            if result == "" then
                            else
                                -- Если ошибка - оставляем сделку в файле
                                table.insert(updated_lines, line)
                            end
                        end
                    else
                        -- Все остальные строки оставляем как есть
                        table.insert(updated_lines, line)
                    end
                end

                -- Перезаписываем order.txt без выполненых сделок
                local order_file_write = io.open(order_file, "w")
                if order_file_write then
                    for _, line in ipairs(updated_lines) do
                        order_file_write:write(line .. "\n")
                    end
                    order_file_write:close()
                end
            end
        end

        sleep(1000)
    end
end

function OnStop()
    is_run = false
end