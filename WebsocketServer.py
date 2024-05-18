#!/usr/bin/env python
import os
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

dataset = pd.read_csv("./heart_attack_prediction_dataset.csv")
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
   result = json.dumps(c)
   return result

async def createPlots(data):
   # Bloodpressure Plots (scatter and bar chart)
   print(data)
   systolics = data['systolicValues']
   diastolics = data['diastolicValues']
   xAxis = np.arange(0, len(systolics), 1)
   dfBP = pd.DataFrame({"Measurements":xAxis, "Systolic": systolics, "Diastolic": diastolics})
   fig = px.line(dfBP, x="Measurements", y=["Systolic", "Diastolic"], title="Bloodpressure Development", markers=True)
   fileBP = f"bp_scatter_{time.time()}.png"
   fig.write_image(f"./{fileBP}", engine="kaleido")

   bpBarDF = pd.DataFrame({"BP": ["Low", "Normal", "High"], "data": [data['bpLow'], data['bpNormal'], data['bpHigh']]})
   fig = px.bar(bpBarDF, x="BP", y="data", color="BP", title="Bloodpressure Bar Chart")
   fileBPBar = f"bp_bar_{time.time()}.png"
   fig.write_image(f"./{fileBPBar}", engine="kaleido")

   # HR Plots (scatter and bar chart)
   hrs = data['hrValues']
   dfHR = pd.DataFrame({"Measurements": xAxis, "HR": hrs})
   fig = px.line(dfHR, x="Measurements", y="HR", title="Heartrate Development", markers=True)
   fileHR = f"hr_scatter_{time.time()}.png"
   fig.write_image(f"./{fileHR}", engine="kaleido")

   hrBarDF = pd.DataFrame({"HR": ["Low", "Normal", "High"], "data": [data['hrLow'], data['hrNormal'], data['hrHigh']]})
   fig = px.bar(hrBarDF, x="HR", y="data", color="HR", title="Heartrate Bar Chart")
   fileHRBar = f"hr_bar_{time.time()}.png"
   fig.write_image(f"./{fileHRBar}", engine="kaleido")

   # Stress Level Plots (scatter and bar chart)
   stress = data['stressValues']
   dfStress = pd.DataFrame({"Measurements":xAxis, "Stress Level": stress})
   fig = px.line(dfStress, x="Measurements", y="Stress Level", title="Stress Level", markers=True)
   fileStress = f"stress_scatter_{time.time()}.png"
   fig.write_image(f"./{fileStress}", engine="kaleido")

   stressBarDF = pd.DataFrame({"Stress": ["Low", "Normal", "High"], "data": [data['stressLow'], data['stressNormal'], data['stressHigh']]})
   fig = px.bar(stressBarDF, x="Stress", y="data", color="Stress", title="Stress Level Bar Chart")
   fileStressBar = f"stress_bar_{time.time()}.png"
   fig.write_image(f"./{fileStressBar}", engine="kaleido")
   return [fileBP, fileBPBar, fileHR, fileHRBar, fileStress, fileStressBar]

async def createPDF(text):
   images = await createPlots(text)
   counter = 0
   plots = ""
   for img in images:
       plots += f"![alt text](./{img})\n\n"
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
   obese = "obese" if text['obesity'] == "1" else "non-obese"
   diabetes = "yes" if text['diabetes'] == "1" else "no"
   familyHistory = "yes" if text['familyHistory'] == "1" else "no"
   medicationUser = "yes" if text['medicationUse'] == "1" else "no"
   heartProblems = "yes" if text['heartProblems'] == "1" else "no"
   exerciseH = text['exerciseHours']
   name = f"**Name:** {text['firstName']} {text['lastName']}\n\n" if text['firstName'] != "" and text['lastName'] != "" else ""
   patientID = f"**Patient-ID:** {text['patientID']}\n\n" if text['patientID'] != "" or text['patientID'] != None else ""
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
   pdf.add_section(Section(f"### Follow up\n\nGenerated Text from LLM"))
   pdf.meta["title"] = "Health Report"
   pdf.meta["author"] = "HoloMatik.AI"
   t = time.time()
   fileName = f"{t}_{text['patientID']}.pdf"
   pdf.save(f"./{fileName}")
   return fileName, images

async def health_check(path, request_headers):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"


async def handler(websocket):
    async for message in websocket:
        msg = json.loads(message)
        if msg['type'] == "delete":
            f = msg['file']
            print(f)
            cmd = f'sudo rm ./{f}'
            cmd2 = f"sudo rm "
            for img in images:
                cmd2 += f"./{img} "
            print(cmd2)
            await asyncio.sleep(10)
            os.system(cmd)
            os.system(cmd2)
            #d = Timer(10.0, os.system(cmd))
            #d.start()
            #os.system(f"sudo rm ./server/{f[1]}")
        elif msg['type'] == "sample":
            respMsg = await sampleExample()
            print(respMsg)
            await websocket.send(respMsg)
        elif msg['type'] == "pdf":
            file, images = await createPDF(msg)
            resp = {"type": "pdf", "src": f"https://holomatik-ai.onrender.com/{file}"}
            rep = json.dumps(resp)
            #TODO: LLM prediction with LLM. Adding generated text to pdf
            await websocket.send(rep)
        elif msg['type'] == "rating":
            print(f"The rating was: {msg['rating']}")

'''
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name("cert.pem")
localhost_key = pathlib.Path(__file__).with_name("key.pem")
ssl_context.load_cert_chain(localhost_pem, keyfile=localhost_key)
'''

async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    #port = int(os.environ.get("PORT", "8001"))
    async with websockets.serve(handler, "", 8080, process_request=health_check):
        await stop


if __name__ == "__main__":
    asyncio.run(main())
