from telegram import Update
from telegram.ext import CallbackContext

from Auth import permLevel
from Database import addGym, deleteGym, findGym, getUser
from Functions import sanification
from JSONParser import getConfig, getListaRaid, getPermessi, loadJSON, updateListaRaid

def admin(update: Update, context: CallbackContext):
	#ATTENZIONE! Solo una persona con permesso pari a 4 o superiore nel Database può assegnare Admin! Non esiste un comando per questo
	changePermission(update, context, 4, 3, True)

def ban(update: Update, context: CallbackContext):
	changePermission(update, context, 3, -1)

def changePermission(update: Update, context: CallbackContext, minPerm: int, Autorizzazione: int, Reset: bool = False):
	if permLevel(update.message.from_user.id) < minPerm:
		return
	command = sanification(update.message.text, True).split()
	if len(command) == 1:
		context.bot.sendMessage(chat_id = update.message.chat_id, text = f"{command[0]} ID/username/nickname")
	else:
		target = (getUser(int(command[1])) if command[1].isdigit() else getUser(None, command[1])) if len(command) > 1 else None
		if len(command) > 1 and (not target):
			context.bot.sendMessage(chat_id = update.message.chat_id, text = "Utente non trovato")
		elif target.Autorizzazione >= permLevel(update.message.from_user.id):
			context.bot.sendMessage(chat_id = update.message.chat_id, text = "Non puoi cambiare i permessi di chi è del tuo stesso livello")
		else:
			target.Autorizzazione = Autorizzazione if (target.Autorizzazione != Autorizzazione or (not Reset)) else 1
			target.setAuthorization(Autorizzazione)
			context.bot.sendMessage(chat_id = update.message.chat_id, text = f"{target.Username if target.Username else target.Nome} è ora {getPermessi()[str(target.Autorizzazione)]}")

def eliminapalestra(update: Update, context: CallbackContext):
	if permLevel(update.message.from_user.id) < 3:
		return
	filters = []
	command = sanification(update.message.text).split()
	for i in range (1, len(command)):
		filters.append(f'%{command[i].lower()}%')
	Palestre = findGym(filters)
	config = getConfig()
	if len(Palestre) == 0:
		return context.bot.sendMessage(chat_id = update.message.chat_id, text = f"""Nessuna palestra trovata{f" col nome {' '.join(command[1:])}" if len(command) > 1 else ""}""")
	if len(Palestre) == 1:
		deleteGym(Palestre[0][0])
		if config["mappa"]:
			context.bot.sendLocation(chat_id = update.message.chat_id, longitude = Palestre[0][2], latitude = Palestre[0][3])
		return context.bot.sendMessage(chat_id = update.message.chat_id, text = f"Palestra eliminata! (#{Palestre[0][0]}):{chr(10)}{Palestre[0][1]}{chr(10)}<code>{Palestre[0][3]}, {Palestre[0][2]}</code>", parse_mode = "HTML")
	toSendText = f"""Troppe palestre trovate {f" col nome {' '.join(command[1:])}" if len(command) > 1 else ""}"""
	for i in range(0, min(50, len(Palestre))):
		toSendText += f"{chr(10)}- {Palestre[i][1]} (#{Palestre[i][0]})"
	return context.bot.sendMessage(chat_id = update.message.chat_id, text = toSendText)

def idchat(update: Update, context: CallbackContext):
	if permLevel(update.message.from_user.id) < 3:
		return
	return context.bot.sendMessage(chat_id = update.message.chat_id, text = f"IDChat:\n{update.message.chat_id}")

def listaraid(update: Update, context: CallbackContext):
	if permLevel(update.message.from_user.id) < 3:
		return
	command = update.message.text.split()
	lista = getListaRaid()
	if len(command) == 2 or (len(command) > 1 and not (command[1].isdigit())):
		return context.bot.sendMessage(chat_id = update.message.chat_id, text = "Per cambiare una lista usa:\n/listaraid (LV) Pokemon1,Pokemon2,Pokemon3")
	if len(command) == 1:
		toSendText = "<b>Lista Raid Boss</b>"
	else:
		livello = max(min(6, int(command[1])), 1)
		pokemon = ''.join(sanification(update.message.text).split()[2:]).split(',')
		lista[str(livello)] = pokemon
		updateListaRaid(lista)
		toSendText = "<b>Lista Raid Boss</b> aggiornata!"
	for lev in lista:
		toSendText += f"{chr(10)}<i>Livello {lev}</i>:{chr(10)}"
		for pok in lista[lev]:
			toSendText += f" {pok}"
	return context.bot.sendMessage(chat_id = update.message.chat_id, text = toSendText, parse_mode = "HTML")

def palestra(update: Update, context: CallbackContext):
	if permLevel(update.message.from_user.id) < 3:
		return
	reply = update.message.reply_to_message
	if not reply:
		return context.bot.sendMessage(chat_id = update.message.chat_id, text = "Rispondi ad un messaggio contenente la posizione, possono anche essere coordinte del tipo:\n<11.214123, 44.125422>")
	elif reply.location:
		posizione = [reply.location.longitude, reply.location.latitude]
	else:
		coords = reply.text.replace("<", "").replace(">", "").replace(".", "").split(",")
		if not (len(coords) == 2 and coords[0].isdigit() and coords[1].isdigit()):
			return context.bot.sendMessage(chat_id = update.message.chat_id, text = "Scrivi le coordinate in un messaggio quotato nel formato:\n<11.214123, 44.125422>\noppure\n11.214123, 44.125422")
		coords = reply.text.replace("<", "").replace(">", "").split(",")
		posizione = [float(coords[1]), float(coords[0])]
	filters = []
	command = sanification(update.message.text).split()
	for i in range (1, len(command)):
		filters.append(f'%{command[i].lower()}%')
	Palestre = findGym(filters)
	if len(Palestre) != 0:
		context.bot.sendMessage(chat_id = update.message.chat_id, text = "Ho trovato altre palestre con quel nome, avranno nomi simili!")
	nome = ' '.join(filters).replace("%","")[:50]
	IDPalestra = addGym(nome, posizione)
	context.bot.sendLocation(chat_id = update.message.chat_id, longitude = posizione[0], latitude = posizione[1])
	return context.bot.sendMessage(chat_id = update.message.chat_id, text = f"Nuova palestra! (#{IDPalestra}):{chr(10)}{nome}{chr(10)}<code>{posizione[0]}, {posizione[1]}</code>", parse_mode = "HTML")

def proprietario(update: Update, context: CallbackContext):
	utente = getUser(update.message.from_user.id)
	BotInfos = loadJSON("Bot.json")
	if BotInfos["Owner"] == update.message.from_user.id:
		utente.setAuthorization(4)
		context.bot.sendMessage(chat_id = update.message.chat_id, text = f"{utente.Username} è ora {getPermessi()[str(utente.Autorizzazione)]}")

def unban(update: Update, context: CallbackContext):
	changePermission(update, context, 3, 1)

def verifica(update: Update, context: CallbackContext):
	changePermission(update, context, 3, 2)