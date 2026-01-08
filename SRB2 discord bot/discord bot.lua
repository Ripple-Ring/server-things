
-- messiest code ever
-- but it seems to work!!
-- and working is good enough for this case

local password = P_RandomFixed() -- wow, so secure

local DCBOT_DISCORDMSG = 0 -- message coming from discord
local DCBOT_SRB2MSG = 1 -- message coming from srb2
local DCBOT_BUFFERCOUNT = 128

/*local dc_checkdelay = CV_RegisterVar({ -- TODO: work on cvars l8r
    name = "discordbot_delaycheck",
    defaultvalue = 1,

})*/

local messages = {
    [DCBOT_DISCORDMSG] = {},
    [DCBOT_SRB2MSG] = {}
}

local discord_localmsgs = {} -- the local messages read from the discord thing

addHook("NetVars", function(net)
    password = net($)
    messages.globalvars = net($)
end)

---@param p player_t
---@param type integer
---@param msg string
addHook("PlayerMsg", function(p, type, _, msg)
    if not msg
    or (type ~= 0 and type ~= 3) then return end

    local message
    if type == 0 then
        local name = p.name
        local prefix = (p == server and "~") or (IsPlayerAdmin(p) and "@") or ""
        if p == server
        and isdedicatedserver then
            name = "SERVER"
        end

        message = "<" + prefix + name + "> " + msg
    elseif type == 3 then
        message = "CSAY > " + msg
    end

    messages.globalvars[DCBOT_SRB2MSG][#messages.globalvars[DCBOT_SRB2MSG]+1] = message
    COM_BufAddText(server, "srb2todc_msg " + password)
end)

COM_AddCommand("srb2todc_msg", function(p, pword)
    if p ~= server
    or not #messages[DCBOT_SRB2MSG]
    or tonumber(pword) ~= password then return end

    local file = io.openlocal("client/srb2-chatbot/srb2-messages.txt", "a")

    if not file then return end

    for i = 1, #messages[DCBOT_SRB2MSG] do
        if messages[DCBOT_SRB2MSG][i] then
            file:write(messages[DCBOT_SRB2MSG][i] + "\n")
            messages[DCBOT_SRB2MSG][i] = nil
        end
    end

    file:close()
end)

local discord_prefix = "\132[DISCORD]\128 "
local discord_format = "<%s> %s"

local buffer = {}
local function handleBuffer()
    if buffer[leveltime] then
        COM_BufInsertText(server, buffer[leveltime])
        buffer[leveltime] = nil
    end
end

local function addToBuffer(cmd)
    local curtime = leveltime+1

    while buffer[curtime] do
        curtime = $+1
    end

    buffer[curtime] = cmd
end

addHook("ThinkFrame", function()
    if (leveltime % TICRATE) == 0 then
        COM_BufAddText(server, "dctosrb2_load " + password)
    end

    handleBuffer()
end)

COM_AddCommand("dctosrb2_msg", function(p, pword, done, msg, id)
    if p ~= server
    or not (#messages[DCBOT_DISCORDMSG] or msg)
    or tonumber(pword) ~= password then return end

    done = $ == "1" and true or false

    if done then
        print(#messages[DCBOT_DISCORDMSG])
        for i = 1, #messages[DCBOT_DISCORDMSG] do
            if messages[DCBOT_DISCORDMSG][i] then
                local remaining = discord_prefix + messages[DCBOT_DISCORDMSG][i]:gsub("\\q", '"')
                local sfx = true

                while #remaining do
                    chatprint(remaining:sub(1, 255), sfx)

                    remaining = remaining:sub(256)
                    sfx = false
                end

                messages[DCBOT_DISCORDMSG][i] = nil
            end
        end
    elseif msg then
        messages[DCBOT_DISCORDMSG][tonumber(id)] = $ and ($ + msg) or msg
    end
end)

COM_AddCommand("dctosrb2_load", function(p, pword, buffer)
    if p ~= server
    or tonumber(pword) ~= password then return end

    if buffer and #discord_localmsgs then
        for i = 1, #discord_localmsgs do
            local msg = discord_localmsgs[i]:gsub('"', "\\q") ---@type string

            while #msg do
                addToBuffer("dctosrb2_msg " + password + " 0 \"" + msg:sub(1, DCBOT_BUFFERCOUNT-1) + "\" " + i)

                msg = msg:sub(DCBOT_BUFFERCOUNT)
            end

            discord_localmsgs[i] = nil
        end
        addToBuffer("dctosrb2_msg " + password + " 1")
    else
        local file = io.openlocal("client/srb2-chatbot/discord-messages.txt", "r")

        if not file then return end

        local foundsomething = false
        for line in file:lines("a") do
            for user, msg in line:gmatch("{{(.+)}} = {{(.+)}}") do
                if #msg > 255 then
                    msg = msg:sub(1, 252) + "..."
                end

                discord_localmsgs[#discord_localmsgs+1] = discord_format:format(user, msg)
                foundsomething = true
            end
        end

        if not foundsomething then return end

        io.openlocal("client/srb2-chatbot/discord-messages.txt", "w"):close()
        COM_BufAddText(server, "dctosrb2_load " + password + " g")
    end
end, COM_LOCAL)