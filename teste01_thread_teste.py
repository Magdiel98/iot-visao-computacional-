import logging
import telebot
import cv2
import threading
import mediapipe as mp
from time import time
from time import sleep
from Adafruit_IO import RequestError, Client, Feed
from datetime import datetime
import socket
import numpy


chave_api = ""

ADAFRUIT_IO_USERNAME = ""
ADAFRUIT_IO_KEY = ""

url = 'http://...:/stream'

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

bot = telebot.TeleBot(chave_api)
valor = 0

webcam = cv2.VideoCapture(2)
solucao_reconhecimento_rosto = mp.solutions.face_detection
reconhecedor_rostos = solucao_reconhecimento_rosto.FaceDetection()
desenho = mp.solutions.drawing_utils

tempo = 0
inicio = time()
final = time()
cont = 0
cont2 = 0
cont3 = 0
formato = "%H:%M:%S"
tempo_formatado = 0
hora_inicio = 0
hora_final = 0

telebot.apihelper.READ_TIMEOUT = 10

@bot.message_handler(commands=["foto"])
def foto(mensagem):
  try:
    rt, fra = webcam.read()
    cv2.imwrite("Imagem\FotoCam.png", fra)
    bot.send_photo(chat_id=mensagem.chat.id, photo=open("Imagem\FotoCam.png", 'rb'))
    #timeout = 10
  except Exception as e:
      logging.exception(e)
      sleep(5)
      foto(mensagem)


@bot.message_handler(func=lambda mensagem: True)
def responder(mensagem):
  try:
    texto = """Para tirar foto: 
               /foto
             """
    bot.send_message(mensagem.chat.id, texto)
  except Exception as e:
      logging.exception(e)
      sleep(5)
      responder(mensagem)


def camera():
    global cont, cont2, cont3
    global tempo
    global inicio, final
    global tempo_formatado
    global formato
    global hora_final, hora_inicio

    if webcam.isOpened():
        #validacao, frame = webcam.read()#Pega a informação que vem da câmera
        # print("Conectou") Apenas para printar no console
        while True:
            validacao, frame = webcam.read()

            lista_rostos = reconhecedor_rostos.process(frame)
            if lista_rostos.detections:
                if cont3 == 0:
                    try:
                        presenca = aio.feeds("presenca")
                    except RequestError:
                        presenca_feed = Feed(name="presenca")
                        presenca_feed = aio.create_feed(presenca_feed)
                    aio.send_data(presenca.key, 1)
                    cont3 = 1

                if cont == 1:
                    bot.send_message(-4083967750, "Há alguém na recepção")
                    try:
                        presenca = aio.feeds("presenca")
                    except RequestError:
                        presenca_feed = Feed(name="presenca")
                        presenca_feed = aio.create_feed(presenca_feed)
                    aio.send_data(presenca.key, 1)

                    horaf = datetime.now()
                    segundos_inteiros = int(horaf.strftime("%S"))

                    hora_final = horaf.strftime(formato)[:-2] + f'{segundos_inteiros:02d}'

                    data = datetime.now().date().strftime("%Y-%m-%d")

                    try:
                        tim = aio.feeds("tempo")
                    except RequestError:
                        tim_feed = Feed(name="tempo")
                        tim_feed = aio.create_feed(tim_feed)
                    aio.send_data(tim.key, f'Tempo ausente: {tempo_formatado} Hora da saída: {hora_inicio} Hora da volta: {hora_final} Data: {data}')

                    #Armazenar dados:
                    arquivo = open('Arquivo/infor.txt', 'a')
                    info = f'Tempo ausente: {tempo_formatado} Hora da saida: {hora_inicio} Hora da volta: {hora_final} Data: {data}\n'
                    arquivo.write(info)
                    arquivo.close()


                tempo = 0
                cont = 0
                inicio = time()
                for rosto in lista_rostos.detections:
                    desenho.draw_detection(frame, rosto)
            else:
                final = time()
                tempo = final - inicio

                horas, restante = divmod(tempo, 3600)
                minutos, segundos = divmod(restante, 60)
                tempo_formatado = "{:02}:{:02}:{:02}".format(int(horas), int(minutos), int(segundos))

                if cont2 == 0:
                    horai = datetime.now()
                    segundos_inteiros = int(horai.strftime("%S"))

                    hora_inicio = horai.strftime(formato)[:-2] + f'{segundos_inteiros:02d}'

                    cont2 = 1


                if tempo >= 10 and cont == 0:
                    bot.send_message(-4083967750, "Não há ninguém na recepção")
                    try:
                        presenca = aio.feeds("presenca")
                    except RequestError:
                        presenca_feed = Feed(name="presenca")
                        presenca_feed = aio.create_feed(presenca_feed)
                    aio.send_data(presenca.key, 0)

                    cont = 1

            cv2.imshow("Video da Webcam", frame) #mostra a imagem
            key = cv2.waitKey(5) #espera uma certa quantidade de segundos a variável key
                                 #armazenará a informação as teclas clicadas no teclado
            if key == 27:
                break

    webcam.release() #finaliza a conexão com a câmera
    cv2.destroyAllWindows() #garantir que a imagem será fechada

try:
    threading.Thread(target=camera).start()
except Exception as e:
    logging.exception(e)
    sleep(5)
    print("Problemas com a câmera")
    threading.Thread(target=camera).start()



try:
    bot.polling() #looping infinito que faz com que o bot converse o tempo
              #com o telegram
except Exception as e:
    logging.exception(e)
    sleep(5)
    bot.polling()


#decorator serve para atribuir uma nova funcionalidade para a função abaixo
