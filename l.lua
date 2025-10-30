-- multi_price.lua
is_run = true

function main()
    -- Простой путь без русских букв
    local file_path = "C:/QUIK_DATA/price.txt"

    -- Коды инструментов
    local instruments = {
        {class = "SPBFUT", ticker = "GLDRUBF", code = "GLDRUBF"},
        {class = "SPBFUT", ticker = "IMOEXF", code = "IMOEXF"}
    }

    message("Start writing prices", 1)

    while is_run do
        local price_strings = {}

        -- Получаем цены для всех инструментов
        for i, instr in ipairs(instruments) do
            local price_data = getParamEx(instr.class, instr.ticker, "LAST")

            if price_data and price_data.param_value and price_data.param_value ~= "" then
                table.insert(price_strings, instr.code .. ":" .. price_data.param_value)
            end
        end

        -- Формируем итоговую строку
        if #price_strings > 0 then
            local content = table.concat(price_strings, " ")

            -- Записываем в файл
            local file = io.open(file_path, "w")
            if file then
                file:write(content)
                file:close()
            end

            -- Логируем для отладки (раз в 10 секунд)
            if math.fmod(os.time(), 10) == 0 then
            end
        else
            message("No price data available", 2)
        end

        sleep(1000)
    end
end

function OnStop()
    is_run = false
    message("Script stopped", 1)
end