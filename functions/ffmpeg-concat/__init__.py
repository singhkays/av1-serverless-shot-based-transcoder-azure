import logging
import json

import azure.functions as func

# This function is used to create a concat file as per the ffmpeg concat demuxer schema
# https://trac.ffmpeg.org/wiki/Concatenate#demuxer


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    body = req.get_body()
    aciShotsVideoPath = req.headers.get('aciShotsVideoPath')    

    # Fail if no request body passed
    if not body:
        return func.HttpResponse(
             "Please pass in the request body",
             status_code=400
        )

    if not (aciShotsVideoPath):
        return func.HttpResponse(
             "Please pass required parameters in the request body",
             status_code=400
        )

    shots = json.loads(body)
    returnString = ''

# We're creating a concat file for ffmpeg demuxer
# See example schema here https://trac.ffmpeg.org/wiki/Concatenate#demuxer 

    for shot in shots:
        # If we're at last shot, then don't add a new line
        if shot == shots[-1]:
            returnString += "file '{}{}.mkv'".format(aciShotsVideoPath, shot['id'])
        else:
            returnString += "file '{}{}.mkv'\n".format(aciShotsVideoPath, shot['id'])

    return func.HttpResponse(
             returnString,
             status_code=200
        )