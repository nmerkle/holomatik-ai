#!/usr/bin/env python
import os
import base64
import signal
import json
import time
import http
from markdown_pdf import MarkdownPdf
from markdown_pdf import Section
import asyncio
import websockets
import ssl
import pathlib
import plotly.express as px
import numpy as np
import pandas as pd
import random
import functools
import math

os.mkdir("./temp")
dataset = pd.read_csv("./heart_attack_prediction_dataset.csv")
with open("./dataset.json", "r") as jsonFile:
    jsonData = jsonFile.read()
    reports = json.loads(jsonData)

js = json.loads(dataset.to_json(orient="records"))

async def sampleExample():
   index = random.randint(0, len(dataset))
   print(f"Index: {index}")
   sample = dataset.iloc[index, :]
   print(f"Sample: {sample}")
   c = dict()
   for col in js[index]:
      print(col)
      c[col] = js[index][col]
      print(col)
   c['type'] = "sample"
   c['index'] = index
   #result = json.dumps(c)
   return c

async def createPlots(data):
   # Bloodpressure Plots (scatter and bar chart)
   print(data)
   systolics = data['systolicValues']
   diastolics = data['diastolicValues']
   xAxis = np.arange(0, len(systolics), 1)
   dfBP = pd.DataFrame({"Measurements":xAxis, "Systolic": systolics, "Diastolic": diastolics})
   fig = px.line(dfBP, x="Measurements", y=["Systolic", "Diastolic"], title="Bloodpressure Development", markers=True)
   fileBP = f"bp_scatter_{time.time()}.png"
   fig.write_image(f"./temp/{fileBP}", engine="kaleido")

   bpBarDF = pd.DataFrame({"BP": ["Low", "Normal", "High"], "data": [data['bpLow'], data['bpNormal'], data['bpHigh']]})
   fig = px.bar(bpBarDF, x="BP", y="data", color="BP", title="Bloodpressure Bar Chart")
   fileBPBar = f"bp_bar_{time.time()}.png"
   fig.write_image(f"./temp/{fileBPBar}", engine="kaleido")

   # HR Plots (scatter and bar chart)
   hrs = data['hrValues']
   dfHR = pd.DataFrame({"Measurements": xAxis, "HR": hrs})
   fig = px.line(dfHR, x="Measurements", y="HR", title="Heartrate Development", markers=True)
   fileHR = f"hr_scatter_{time.time()}.png"
   fig.write_image(f"./temp/{fileHR}", engine="kaleido")

   hrBarDF = pd.DataFrame({"HR": ["Low", "Normal", "High"], "data": [data['hrLow'], data['hrNormal'], data['hrHigh']]})
   fig = px.bar(hrBarDF, x="HR", y="data", color="HR", title="Heartrate Bar Chart")
   fileHRBar = f"hr_bar_{time.time()}.png"
   fig.write_image(f"./temp/{fileHRBar}", engine="kaleido")

   # Stress Level Plots (scatter and bar chart)
   stress = data['stressValues']
   dfStress = pd.DataFrame({"Measurements":xAxis, "Stress Level": stress})
   fig = px.line(dfStress, x="Measurements", y="Stress Level", title="Stress Level", markers=True)
   fileStress = f"stress_scatter_{time.time()}.png"
   fig.write_image(f"./temp/{fileStress}", engine="kaleido")

   stressBarDF = pd.DataFrame({"Stress": ["Low", "Normal", "High"], "data": [data['stressLow'], data['stressNormal'], data['stressHigh']]})
   fig = px.bar(stressBarDF, x="Stress", y="data", color="Stress", title="Stress Level Bar Chart")
   fileStressBar = f"stress_bar_{time.time()}.png"
   fig.write_image(f"./temp/{fileStressBar}", engine="kaleido")
   return [fileBP, fileBPBar, fileHR, fileHRBar, fileStress, fileStressBar]

async def createPDF(index, text):
   images = await createPlots(text)
   counter = 0
   plots = ""
   for img in images:
       plots += f"![alt text](./temp/{img})\n\n"
       print(plots)
       counter += 1
   stdSystolic = functools.reduce(lambda a, b: math.sqrt((a-text['meanSystolicValue'])**2)+math.sqrt((b-text['meanSystolicValue'])**2), text['systolicValues'])
   stdSystolic /= (len(text['systolicValues'])-1)
   stdDiastolic = functools.reduce(lambda a, b: math.sqrt((a-text['meanDiastolicValue'])**2)+math.sqrt((b-text['meanDiastolicValue'])**2), text['diastolicValues'])
   stdDiastolic /= (len(text['diastolicValues'])-1)
   stdHR = functools.reduce(lambda a, b: math.sqrt((a-text['meanHR'])**2)+math.sqrt((b-text['meanHR'])**2), text['hrValues'])
   stdHR /= (len(text['hrValues'])-1)
   stdStress = functools.reduce(lambda a, b: math.sqrt((a-text['meanStress'])**2)+math.sqrt((b-text['meanStress'])**2), text['stressValues'])
   stdStress /= (len(text['stressValues'])-1)
   smoker = "smoker" if text['smoker'] == "1" else "non-smoker"
   print(f"Obesity: {text['obesity']}")
   obese = "obese" if text['obesity'] == "1" else "non-obese"
   diabetes = "yes" if text['diabetes'] == "1" else "no"
   familyHistory = "yes" if text['familyHistory'] == "1" else "no"
   medicationUser = "yes" if text['medicationUse'] == "1" else "no"
   heartProblems = "yes" if text['heartProblems'] == "1" else "no"
   exerciseH = text['exerciseHours']
   name = f"**Name:** {text['firstName']} {text['lastName']}\n\n" if text['firstName'] != "" and text['lastName'] != "" else ""
   patientID = f"**Patient-ID:** {text['patientID']}\n\n" if text['patientID'] != "" or text['patientID'] != None else ""
   report = reports[int(index)]['report'][0:reports[int(index)]['report'].index('<|eot_id|>')]
   patient_profile = (
   f"{name}{patientID}**Age:** {text['age']}\n\n**Gender:** {text['sex']}\n\n**Income per year:** {text['income']}\n\n**Country:** {text['country']}\n\n**Continent:** {text['continent']}\n\n"
   f"**Diabetes:** {diabetes}\n\n**Cholesterol:** {text['cholesterol']} mg/dl\n\n**Triglycerid:** {text['triglycerid']} mg/dl\n\n**Smoking Status:** {smoker}\n\n"
   f"**Heart Disease in Family History:** {familyHistory}\n\n**Weight-Status:** {obese}\n\n**BMI:** {round(text['bmi'], 2)}\n\n**Medication Use:** {medicationUser}\n\n**Previous Heartproblems:** {heartProblems}\n\n"
   )
   patient_activity = (
   f"**Exercise Hours per Week:** {round(exerciseH, 2)}\n\n**Physical Activity Days per Week:** {text['activityDays']}\n\n**Sedentary Hours per Day:** {round(text['sedentaryHours'], 2)}\n\n"
   f"**Sleep Hours per Day:** {text['sleepHoursPerDay']}\n\n**Alcohol Consumption:** {text['alcoholConsumption']}\n\n**Diet Style:** {text['diet']}\n\n"
   )
   meanTxt = (
   f"**Mean Systolic Value:** {round(text['meanSystolicValue'], 2)}\t\t **Standard Deviation:** {round(stdSystolic, 2)}\n\n"
   f"**Mean Diastolic Value:** {round(text['meanDiastolicValue'], 2)}\t\t**Standard Deviation:** {round(stdDiastolic, 2)}\n\n"
   f"**Mean Heartrate:** {round(text['meanHR'], 2)}\t\t**Standard Deviation:** {round(stdHR, 2)}\n\n"
   f"**Mean Stress Level:** {round(text['meanStress'], 2)}\t\t**Standard Deviation:** {round(stdStress,2)}\n\n"
   f"**Number of Measurements:** {text['simulationSteps']}\n\n"
   )
   pdf = MarkdownPdf(toc_level=2)
   pdf.add_section(Section(f"# Health Report ({text['date']})\n\n## Patient Profile\n\n{patient_profile}\n"), user_css="h1 {text-align:center;}")
   pdf.add_section(Section(f"## Patient Activity and Life-Style\n\n{patient_activity}\n\n\n## Vital Sign Measurements\n\n{meanTxt}{plots}\n\n"), user_css="h2, h3 {text-align:left;}")
   #pdf.add_section(Section(f"### Medical History\n\n{meanTxt}{plots}\n\n### Recommendations\n\nGenerated Text from LLM"), user_css="h2, h3 {text-align:left;}")
   pdf.add_section(Section(f"### Generated Text from LLM\n\n{report}"))
   pdf.meta["title"] = "Health Report"
   pdf.meta["author"] = "HoloMatik.AI"
   t = time.time()
   fileName = f"{t}_{text['patientID']}.pdf"
   pdf.save(f"./temp/{fileName}")
   return fileName, images

async def encodePDF(file):
   with open(file, 'rb') as pdf_file:
       pdf_binary_data = pdf_file.read()
   pdf_base64_encoded = base64.b64encode(pdf_binary_data)
   pdf_string = pdf_base64_encoded.decode("ascii")
   return pdf_string

async def health_check(path, request_headers):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"


async def handler(websocket):
    images = None
    pointer = None
    async for message in websocket:
        msg = json.loads(message)
        if msg['type'] == "delete":
            f = msg['file']
            print(f)
            cmd = f'rm ./temp/{f}'
            cmd2 = f"rm "
            for img in images:
                cmd2 += f"./temp/{img} "
            print(cmd2)
            await asyncio.sleep(10)
            os.system(cmd)
            os.system(cmd2)
        elif msg['type'] == "sample":
            respMsg = await sampleExample()
            result = json.dumps(respMsg)
            print(result)
            pointer = int(respMsg['index'])
            print(pointer)
            await websocket.send(result)
        elif msg['type'] == "pdf":
            file, images = await createPDF(pointer, msg)
            enc_base64_pdf = await encodePDF(f"./temp/{file}")
            resp = {"type": "pdf", "file": file, "src": f"data:application/pdf;base64,{enc_base64_pdf}"}
            rep = json.dumps(resp)
            #TODO: LLM prediction with LLM. Adding generated text to pdf
            await websocket.send(rep)
        elif msg['type'] == "rating":
            print(f"The rating was: {msg['rating']}")
            #js[index]['numRatings'] = 1 if "numRatings" not in js[index] else js[index]['numRatings'] = js[index]['numRatings'] + 1
            #js[index]['rating'] = int(msg['rating']) if "rating" not in js[index] else js[index]['rating'] = (js[index]['rating'] + int(msg['rating'])) / js[index]['numRatings']

async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    async with websockets.serve(handler, "", 8080, process_request=health_check):
        await stop


if __name__ == "__main__":
    asyncio.run(main())
