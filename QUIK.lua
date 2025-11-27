-- executive_script.lua

-- PRICES:GLDRUBF/ЦЕНА; IMOEXF/ЦЕНА
-- DEAL:ticker/operation/QUANTITY
is_run = true

function main()
    local executive_file = "C:/QUIK_DATA/executive.txt"

    -- Коды инструментов для мониторинга цен
    local instruments = {
        {class = "SPBFUT", ticker = "GLDRUBF", code = "GLDRUBF"},
        {class = "SPBFUT", ticker = "IMOEXF", code = "IMOEXF"}
    }

    while is_run do
        -- Читаем весь файл
        local file = io.open(executive_file, "r")
        if file then
            local lines = {}
            local price_lines = {}
            local deal_lines = {}

            -- Разделяем строки по типам
            for line in file:lines() do
                table.insert(lines, line)
                if string.sub(line, 1, 7) == "PRICES:" then
                    table.insert(price_lines, line)
                elseif string.sub(line, 1, 5) == "DEAL:" then
                    table.insert(deal_lines, line)
                end
            end
            file:close()

            -- ОБРАБОТКА ЦЕН: обновляем строку PRICES:
            local price_strings = {}
            for i, instr in ipairs(instruments) do
                local price_data = getParamEx(instr.class, instr.ticker, "LAST")
                if price_data and price_data.param_value and price_data.param_value ~= "" then
                    table.insert(price_strings, instr.code .. "/" .. price_data.param_value)
                end
            end

            local new_price_line = "PRICES:" .. table.concat(price_strings, "; ")

            -- ОБРАБОТКА СДЕЛОК: выполняем и удаляем DEAL:
            local updated_lines = {}
            local deal_executed = false

            for i, line in ipairs(lines) do
                if string.sub(line, 1, 7) == "PRICES:" then
                    -- Заменяем старую строку цен на новую
                    table.insert(updated_lines, new_price_line)
                elseif string.sub(line, 1, 5) == "DEAL:" then
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
                            ["TRANS_ID"] = tostring(os.time() + 1)
                        }

                        local result = sendTransaction(transaction)

                        if result == "" then
                            message("Сделка: " .. ticker .. " " .. operation .. " " .. quantity)
                            deal_executed = true
                        else
                            message("Ошибка: " .. result)
                            -- Если ошибка - оставляем сделку в файле
                            table.insert(updated_lines, line)
                        end
                    end
                else
                    -- Все остальные строки оставляем как есть
                    table.insert(updated_lines, line)
                end
            end

            -- Если не было строки PRICES, добавляем её
            local has_prices = false
            for _, line in ipairs(updated_lines) do
                if string.sub(line, 1, 7) == "PRICES:" then
                    has_prices = true
                    break
                end
            end

            if not has_prices then
                table.insert(updated_lines, 1, new_price_line)
            end

            -- Перезаписываем файл
            local file_write = io.open(executive_file, "w")
            if file_write then
                for _, line in ipairs(updated_lines) do
                    file_write:write(line .. "\n")
                end
                file_write:close()
            end

        end

        sleep(1000)
    end
end

function OnStop()
    is_run = false
    message("Script stopped", 1)
end