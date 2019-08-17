import logging
import json
import copy

import azure.functions as func

# JSON schema to create container instances with the Logic App connector
# We'll fill in the values here using this azure function and define all the container instances to be created programattically
aciStringSchema = """
  {
    "name": "1",
    "properties": {
      "image": "",
      "resources": {
        "requests": {
          "memoryInGB": 1,
          "cpu": 4
        }
      },
      "command": [
        ""
      ],
      "volumeMounts": [
        {
          "name": "",
          "mountPath": "",
          "readOnly": false
        },
        {
          "name": "",
          "mountPath": "",
          "readOnly": false
        }
      ]
    }
  }
"""

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    body = req.get_body()

    # Fail if no request body passed
    if not body:
        return func.HttpResponse(
             "Please pass in the request body",
             status_code=400
        )
        
    shots = json.loads(body)
    aciJsonSchema = json.loads(aciStringSchema)

    # Array of conatiner instances JSON definition objects that we'll return to the ACI Logic App connector
    returnArray = []

    # Get header parameters that are passed in from Logic App ACI connector
    videoName = req.headers.get('videoName')
    ffmpegBinaryPath = req.headers.get('ffmpegBinaryPath')

    aciSourceVideoMountName = req.headers.get('aciSourceVideoMountName')
    aciSourceVideoPath = req.headers.get('aciSourceVideoPath')

    aciDestinationVideoMountName = req.headers.get('aciDestinationVideoMountName')
    aciDestinationVideoPath = req.headers.get('aciDestinationVideoPath')

    dockerImage = req.headers.get('dockerImage')
    requestedMemoryInGB = float(req.headers.get('requestedMemoryInGB'))
    requestedCPUCores = int(req.headers.get('requestedCPUCores'))

    if not (videoName or ffmpegBinaryPath or aciSourceVideoMountName or aciSourceVideoPath or aciDestinationVideoMountName or aciDestinationVideoPath or dockerImage or requestedMemoryInGB or requestedCPUCores):
        # Fail if any of the parameters are missing
        return func.HttpResponse(
             "Please pass required parameters in the request body",
             status_code=400
        )

    for shot in shots:
        containerJson = copy.deepcopy(aciJsonSchema)

        # ffmpeg command that needs to be run by the container instance to encode the video
        # Using ffmpeg -ss and -t parameters, we'll only encode a specific time chunk 
        # The time chunks that we need to encode correspond to the different scene timestamps that we'll get from the video index 
        # To fix the ffmpeg error - "Too many packets buffered for output stream 0:1"
        #   Added -max_muxing_queue_size 1024
        ffmpegCommand = "{}/ffmpeg -i {}{} -v debug -c:v libaom-av1 -crf 22 -b:v 0 -strict experimental -cpu-used 4 -row-mt 1 -tiles 2x1 -c:a copy -max_muxing_queue_size 102400 -ss {} -t {} -y {}{}.mkv"
        formattedFFmpeg = ffmpegCommand.format(ffmpegBinaryPath, aciSourceVideoPath, videoName, shot['instances'][0]['start'], shot['instances'][0]['duration'], aciDestinationVideoPath, shot['id'])
        aciCommand = formattedFFmpeg.split(' ')

        containerJson['name'] = 'shot-' + "{}".format(shot['id'])
        containerJson['properties']['image'] = dockerImage
        containerJson['properties']['resources']['requests']['memoryInGB'] = requestedMemoryInGB
        containerJson['properties']['resources']['requests']['cpu'] = requestedCPUCores
        containerJson['properties']['command'] = aciCommand
        containerJson['properties']['volumeMounts'][0]['name'] = aciSourceVideoMountName
        containerJson['properties']['volumeMounts'][0]['mountPath'] = aciSourceVideoPath
        containerJson['properties']['volumeMounts'][1]['name'] = aciDestinationVideoMountName
        containerJson['properties']['volumeMounts'][1]['mountPath'] = aciDestinationVideoPath
        returnArray.append(containerJson)

    # For testing the returnArray
    #print(returnArray)

    return func.HttpResponse(
             json.dumps(returnArray),
             status_code=200
        )
