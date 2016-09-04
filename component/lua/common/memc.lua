local _M = {}

local memcached = require "resty.memcached"
local resolver = require "common.resolver"

function _M.get_connection()
    if ngx.ctx['memc_conn'] then
        return ngx.ctx['memc_conn']
    end

    local memc, err = memcached:new()
    if not memc then
        ngx.log(ngx.ERR, "failed to instantiate memc: ", err)
    end

    memc:set_timeout(os.getenv("DB_CONN_TIMEOUT"))

    local ip = resolver.find_ip_by_host('cache')
    if not ip then
        ngx.log(ngx.ERR, "failed to found ip addr")
    end

    local ok, err = memc:connect(ip, os.getenv("MEMCACHED_PORT"))
    if not ok then
        ngx.log(ngx.ERR, "failed to connect: " .. err)
    end

    ngx.ctx['memc_conn'] = memc
    return ngx.ctx['memc_conn']
end

function _M.close()
    if ngx.ctx['memc_conn'] then
        local ok, err = ngx.ctx['memc_conn']:set_keepalive()
        if not ok then
            ngx.log(ngx.ERR, "cannot set keepalive: ", err)
        end
    end
end

return _M
