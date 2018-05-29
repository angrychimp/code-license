'use strict'

exports.handler = (event, context, callback) => {
    const request = event.Records[0].cf.request
    const headers = request.headers

    // Rewrite subdomain to user spec in URI
    var domain = request.headers.host[0].value.split('.')
    domain.splice(domain.length - 2)
    var user = domain.pop()
    if (user !== undefined) {
        var uri = request.uri.replace(/^\//, '').split('/')
        request.uri = ['/u', user].concat(uri).join('/')
    }

    callback(null, request)
};
