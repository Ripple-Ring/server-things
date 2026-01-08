
-- messiest code ever
-- but it seems to work!!
-- and working is good enough for this case

local password = P_RandomFixed() -- wow, so secure

local DCBOT_DISCORDMSG = 0 -- message coming from discord
local DCBOT_SRB2MSG = 1 -- message coming from srb2
local DCBOT_BUFFERCOUNT = 128

local dc_checkdelay = CV_RegisterVar({ -- TODO: work on cvars l8r
	name = "discordbot_delaycheck",
	defaultvalue = "0.5",
	flags = CV_FLOAT|CV_NETVAR,
	PossibleValue = CV_Natural
})

local rejointimeout = CV_FindVar("rejointimeout")

local has_started = false -- has the server started already?
local messages = {
	[DCBOT_DISCORDMSG] = {},
	[DCBOT_SRB2MSG] = {}
}

---@param p player_t?
local function isServer(p)
	p = (p and p.valid) and $ or consoleplayer

	return not (p and p.valid)
		or p == server
end

local discord_localmsgs = {} -- the local messages read from the discord thing

addHook("NetVars", function(net)
	password = net($)
	messages = net($)
	has_started = net($)
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

		message = "**[" + prefix + name:gsub("*", "\\*") + "]** " + msg:gsub("*", "\\*")
	elseif type == 3 then
		message = "**CSAY > **" + msg
	end

	messages[DCBOT_SRB2MSG][#messages[DCBOT_SRB2MSG]+1] = message
	COM_BufAddText(server, "srb2todc_msg " + password)
end)

---@param p player_t
---@param pword string
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
end, COM_LOCAL)

local discord_prefix = "\132[DISCORD]\128 "
local discord_format = "<%s> %s"

local buffer = {}
local function handleBuffer()
	if buffer[leveltime] then
		COM_BufInsertText(server, buffer[leveltime])
		buffer[leveltime] = nil
	end
end

---@param cmd string
local function addToBuffer(cmd)
	local curtime = leveltime+1

	while buffer[curtime] do
		curtime = $+1
	end

	buffer[curtime] = cmd
end

addHook("ThinkFrame", function()
	if (leveltime % (FixedRound(TICRATE*dc_checkdelay.value)/FU) ) == 0 then
		COM_BufAddText(server, "dctosrb2_load " + password)
	end

	if not has_started then
		messages[DCBOT_SRB2MSG][#messages[DCBOT_SRB2MSG]+1] = "Server started!"
		COM_BufAddText(server, "srb2todc_msg " + password)
		has_started = true
	end

	handleBuffer()
end)

---@param p player_t
---@param pword string
---@param done string
---@param msg string
---@param id string
COM_AddCommand("dctosrb2_msg", function(p, pword, done, msg, id)
	if p ~= server
	or not (#messages[DCBOT_DISCORDMSG] or msg)
	or tonumber(pword) ~= password then return end

	done = $ == "1" and true or false

	if done then
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

---@param p player_t
---@param pword string
---@param buffer string
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

addHook("GameQuit", function()
	if isServer() then
		local file = io.openlocal("client/srb2-chatbot/srb2-messages.txt", "a")

		if not file then return end

		file:write("Server closed!\n")
		file:close()
	end
end)

---@class player_t
---@field lastquittime tic_t

local joinquit_format = "**%s** %s"

---@param p player_t
addHook("PlayerThink", function(p)
	if p.lastquittime
	and p.quittime == 0 then
		messages[DCBOT_SRB2MSG][#messages[DCBOT_SRB2MSG]+1] = joinquit_format:format(p.name, "has rejoined the game")
		COM_BufAddText(server, "srb2todc_msg " + password)
	elseif p.quittime == 1 then
		messages[DCBOT_SRB2MSG][#messages[DCBOT_SRB2MSG]+1] = joinquit_format:format(p.name, "left the game")
		COM_BufAddText(server, "srb2todc_msg " + password)
	elseif p.jointime == 1 then
		messages[DCBOT_SRB2MSG][#messages[DCBOT_SRB2MSG]+1] = joinquit_format:format(p.name, "has joined the game")
		COM_BufAddText(server, "srb2todc_msg " + password)
	end

	p.lastquittime = p.quittime
end)

---@param p player_t
---@param reason integer
addHook("PlayerQuit", function(p, reason)
	if reason == KR_LEAVE
	and rejointimeout.value ~= 0 then
		return
	end

	local msg = "left the game"
	if reason == KR_KICK then
		msg = "has been kicked"
	elseif reason == KR_PINGLIMIT then
		msg = "left the game (Broke ping limit)"
	elseif reason == KR_SYNCH then
		msg = "left the game (Synch failure)"
	elseif reason == KR_TIMEOUT then
		msg = "left the game (Connection timeout)"
	elseif reason == KR_BAN then
		msg = "has been banned"
	end

	messages[DCBOT_SRB2MSG][#messages[DCBOT_SRB2MSG]+1] = joinquit_format:format(p.name, msg)
	COM_BufAddText(server, "srb2todc_msg " + password)
end)