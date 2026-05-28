'use strict';

exports.handler = (event, context, callback) => {
    const authString = 'Basic ' + new Buffer('ooodev:buildeveryHEIGHTtrust').toString('base64');
    const request = event.Records[0].cf.request;
    const headers = request.headers;
    if (typeof headers.authorization == 'undefined' || headers.authorization[0].value != authString) {
        callback(null, {
            body: 'Unauthorized',
            headers: {
                'www-authenticate': [{ key: 'WWW-Authenticate', value: 'Basic' }]
            },
            status: '401',
            statusDescription: 'Unauthorized',
        });
        return;
    }
    callback(null, request);
};
