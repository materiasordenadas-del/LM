-- LM AI Director - safe observation bridge for SP Football Life 2026 v1.1
--
-- This bridge DOES NOT write to game memory.
-- It records team IDs seen by Sider and gives us a stable, version-safe
-- starting point for reverse engineering Master League state.

local m = {}
local VERSION = "0.1.1-fl26.1.1"
local last_home = nil
local last_away = nil
local observation_path = nil

local function append_line(path, line)
    local file = io.open(path, "a")
    if not file then
        log("[LM AI] could not open observation file: " .. tostring(path))
        return
    end
    file:write(line .. "\n")
    file:close()
end

function m.set_teams(ctx, home_team, away_team)
    -- Sider documents that some events can fire more than once for the same
    -- game action. Ignore consecutive duplicates so the observation file does
    -- not become noisy and misleading during reverse engineering.
    if last_home == home_team and last_away == away_team then
        return
    end

    last_home = home_team
    last_away = away_team
    append_line(
        observation_path,
        string.format("SET_TEAMS,%s,%s", tostring(home_team), tostring(away_team))
    )
    log(string.format("[LM AI] set_teams home=%s away=%s", tostring(home_team), tostring(away_team)))
end

function m.context_reset(ctx)
    append_line(observation_path, "CONTEXT_RESET")
    last_home = nil
    last_away = nil
end

function m.overlay_on(ctx)
    if last_home ~= nil then
        return string.format(
            "LM AI Director %s | OBSERVE | home:%s away:%s",
            VERSION,
            tostring(last_home),
            tostring(last_away)
        )
    end
    return string.format("LM AI Director %s | OBSERVE | waiting for team context", VERSION)
end

function m.init(ctx)
    observation_path = ctx.sider_dir .. "lm_ai_observations.csv"
    append_line(observation_path, "START," .. VERSION)
    ctx.register("set_teams", m.set_teams)
    ctx.register("context_reset", m.context_reset)
    ctx.register("overlay_on", m.overlay_on)
    log("[LM AI] bridge loaded: " .. VERSION)
end

return m
