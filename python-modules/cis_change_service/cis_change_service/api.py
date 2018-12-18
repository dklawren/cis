import json
import logging
from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
from flask_cors import cross_origin
from cis_change_service.common import get_config
from cis_change_service import profile
from cis_change_service.idp import requires_auth
from cis_change_service.idp import AuthError
from cis_change_service import __version__

from cis_publisher import operation


app = Flask(__name__)
config = get_config()
logger = logging.getLogger(__name__)

CORS(
    app,
    allow_headers=(
        'x-requested-with',
        'content-type',
        'accept',
        'origin',
        'authorization',
        'x-csrftoken',
        'withcredentials',
        'cache-control',
        'cookie',
        'session-id',
    ),
    supports_credentials=True
)


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


@app.route('/')
def index():
    return 'Mozilla Change Integration Service Endpoint'


@app.route('/version')
def version():
    response = __version__
    return jsonify(message=response)


@app.route('/change', methods=['GET', 'POST', 'PUT'])
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def change():
    user_profile = request.get_json(silent=True)

    if isinstance(user_profile, str):
        user_profile = json.loads(user_profile)

    logger.info('A json payload was received for user: {}'.format(user_profile['user_id']['value']))
    logger.debug('User profile received.  Detail: {}'.format(user_profile))
    publish = operation.Publish()
    result = publish.to_stream(user_profile)
    logger.debug('The result of the attempt to publish the profile was: {}'.format(result))

    if config('stream_bypass', namespace='cis', default='false') == 'true':
        # Plan on stream integration not working an attempt a write directly to discoverable dynamo.
        # Great for development, seeding the vault, and contingency.
        logger.debug(
            'Stream bypass activated.  Integrating user profile directly to dynamodb for: {}'.format(
                user_profile.get('user_id').get('value')
            )
        )
        vault = profile.Vault(result.get('sequence_number'))
        vault.put_profile(user_profile)
    logger.info('The result of publishing for user: {} is: {}'.format(
            user_profile['user_id']['value'],
            result
        )
    )
    return jsonify(result)


@app.route('/changes', methods=['GET', 'POST', 'PUT'])
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def changes():
    user_profiles = request.get_json(silent=True)
    logger.info('A json list of payloads was received totaling: {}'.format(len(user_profiles)))

    results = []
    for profile in user_profiles:
        profile = json.loads(profile)
        publish = operation.Publish()
        result = publish.to_stream(profile)
        logger.debug('The result of the attempt to publish the profile was: {}'.format(result))

        if config('stream_bypass', namespace='cis', default='false') == 'true':
            # Plan on stream integration not working an attempt a write directly to discoverable dynamo.
            # Great for development, seeding the vault, and contingency.
            logger.debug(
                'Stream bypass activated.  Integrating user profile directly to dynamodb for: {}'.format(
                    user_profile.get('user_id').get('value')
                )
            )
            vault = profile.Vault(result.get('sequence_number'))
            vault.put_profile(profile)
        logger.info('The result of publishing for user: {} is: {}'.format(
                profile['user_id']['value'],
                result
            )
        )
        results.append(result)
    return jsonify(results)


@app.route('/change/status', methods=['GET'])
@cross_origin(headers=['Content-Type', 'Authorization'])
def status():
    sequence_number = request.args.get('sequenceNumber')
    status = profile.Status(sequence_number)
    result = status.all
    return jsonify(result)
