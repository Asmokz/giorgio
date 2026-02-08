import discord
import logging
import asyncio
from discord.ui import View, Button
from discord import ButtonStyle
from config.settings import settings, SecretStr

logger = logging.getLogger(__name__)

class RatingView(View):
    """
    Vue avec boutons 1-10 pour noter un contenu.
    Giorgio a ses opinions sur chaque note...
    """
    
    def __init__(self, user_id: str, content_id: str, content_name: str,  watchlog_id: int):
        super().__init__(timeout=86400)  # 24h pour répondre
        self.user_id = user_id
        self.content_id = content_id
        self.content_name = content_name
        self.watchlog_id = watchlog_id
        self.rating = None
        
        # Crée les boutons 1-10 (deux rangées de 5)
        for i in range(1, 11):
            button = Button(
                label=str(i),
                style=self._get_button_style(i),
                custom_id=f"rating_{i}",
                row=0 if i <= 5 else 1
            )
            button.callback = self._create_callback(i)
            self.add_item(button)
    
    def _get_button_style(self, rating: int) -> ButtonStyle:
        """Couleur du bouton selon la note"""
        if rating <= 3:
            return ButtonStyle.red
        elif rating <= 6:
            return ButtonStyle.grey
        elif rating <= 8:
            return ButtonStyle.blurple
        else:
            return ButtonStyle.green
    
    def _create_callback(self, rating: int):
        """Crée le callback pour chaque bouton"""
        async def callback(interaction: discord.Interaction):
            self.rating = rating
            response = self._get_giorgio_reaction(rating)
            
            # Désactive tous les boutons après le vote
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(
                content=f"✅ Tu as noté **{self.content_name}** : **{rating}/10**\n\n{response}",
                view=self
            )
            
            # Sauvegarde la note en BDD
            from src.services import database_service
            database_service.update_rating(self.watchlog_id, rating)
            
            logger.info(f"⭐ Rating saved: {self.content_name} = {rating}/10")
            
            self.stop()
        
        return callback
    
    def _get_giorgio_reaction(self, rating: int) -> str:
        """La réaction de Giorgio selon la note — il a des opinions!"""
        reactions = {
            1: "🤮 *Madonna!* Une telle insulte au cinéma... J'espère que tu plaisantes, *caro*.",
            2: "😤 *Mamma mia...* Même ma grand-mère ferait un meilleur film avec son téléphone.",
            3: "😒 Bof. Comme des pâtes trop cuites — ça passe, mais c'est triste.",
            4: "🤷 Médiocre. Ni bon ni mauvais, comme un espresso tiède.",
            5: "😐 Pile au milieu... Tu es aussi indécis que moi devant une carte de pizzas.",
            6: "🙂 Pas mal! Ce n'est pas du Fellini, mais ça se regarde.",
            7: "😊 Ah, voilà quelque chose de correct! Tu commences à avoir du goût, *amico*.",
            8: "😍 *Bellissimo!* Ça c'est du cinéma! Mon cœur italien est content.",
            9: "🤩 *Magnifico!* Un chef-d'œuvre! Tu as l'âme d'un vrai cinéphile!",
            10: "🥹 *Perfetto!* Je pleure des larmes de joie... C'est aussi beau que le coucher de soleil sur Venise!"
        }
        return reactions.get(rating, "🤔 *Interessante...*")

class GiorgioBot(discord.Client):
    """
    Giorgio - Un bot italien passionné d'art et de cinéma.
    Il notifie les utilisateurs quand ils finissent un film
    et leur demande de noter ce chef-d'œuvre (ou cette catastrophe).
    """
    
    def __init__(self, channel_id: int):
        intents = discord.Intents.default()
        intents.message_content = True  # Pour lire les mentions
        super().__init__(intents=intents)
        self.channel_id = channel_id
        self.notification_channel = None
    
    async def on_ready(self):
        """Quand Giorgio se connecte"""
        logger.info(f"🤌 Mamma mia! {self.user} è arrivato!")
        self.notification_channel = self.get_channel(self.channel_id)
        if not self.notification_channel:
            logger.error(f"❌ Channel {self.channel_id} not found!")
    
    async def on_message(self, message: discord.Message):
        """Répond quand on mentionne Giorgio"""
        # Ignore ses propres messages
        if message.author == self.user:
            return
        
        # Vérifie si Giorgio est mentionné
        if self.user in message.mentions:
            await self._handle_mention(message)
    
    async def _handle_mention(self, message: discord.Message):
        """Gère les mentions de Giorgio"""
        content = message.content.lower()
        
        if any(word in content for word in ["suggestion", "suggère", "recommande", "quoi regarder", "film", "série"]):
            await self._send_suggestion(message)
        else:
            # Réponse par défaut, très Giorgio
            await message.reply(
                "🤌 *Ciao bello!* Tu m'as appelé mais je ne comprends pas ce que tu veux...\n"
                "Mentionne-moi avec **suggestion** et je te trouverai une œuvre digne de ce nom!"
            )
    
    async def _send_suggestion(self, message: discord.Message):
        """Envoie une suggestion de film/série"""
        # TODO: Intégrer le moteur de suggestions (pour l'instant, réponse placeholder)
        await message.reply(
            "🎬 *Ah, tu veux que Giorgio te guide dans le monde du septième art!*\n\n"
            "Patience, *caro mio*... Mon cerveau de connaisseur est encore en construction. "
            "Bientôt, je te proposerai des chefs-d'œuvre dignes de Fellini! 🇮🇹"
        )
    
    async def send_rating_request(self, user_id: str, username: str, content_id: str, content_name: str, content_type: str, watchlog_id: int):
        """
        Envoie une demande de notation après qu'un utilisateur ait fini un contenu.
        C'est ici que Giorgio brille!
        """
        if not self.notification_channel:
            logger.error("❌ Notification channel not set!")
            return
        
        # Message personnalisé selon le type
        if content_type == "Episode":
            intro = f"📺 *Ecco!* **{username}** vient de terminer un épisode de **{content_name}**!"
        else:
            intro = f"🎬 *Bellissimo!* **{username}** vient de terminer **{content_name}**!"
        
        message_content = (
            f"{intro}\n\n"
            f"Alors, *caro mio*, c'était comment? Note cette œuvre de 1 à 10!\n"
            f"*(1 = mamma mia quelle horreur, 10 = chef-d'œuvre absolu)*"
        )
        
        view = RatingView(user_id, content_id, content_name, watchlog_id)
        
        await self.notification_channel.send(content=message_content, view=view)
        logger.info(f"📤 Rating request sent for {content_name} (user: {username})")

import threading

# Instance globale du bot
_bot_instance: GiorgioBot = None
_bot_loop: asyncio.AbstractEventLoop = None


def start_bot(token: SecretStr, channel_id: int):
    """
    Démarre Giorgio dans un thread séparé.
    Appelé au startup de FastAPI.
    """
    global _bot_instance, _bot_loop
    
    def run_bot():
        global _bot_instance, _bot_loop
        
        # Crée une nouvelle event loop pour ce thread
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)
        
        _bot_instance = GiorgioBot(channel_id)
        
        try:
            _bot_loop.run_until_complete(_bot_instance.start(token))
        except Exception as e:
            logger.error(f"❌ Giorgio crashed: {e}")
    
    # Lance dans un thread daemon (s'arrête quand le programme principal s'arrête)
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    logger.info("🧵 Giorgio bot thread started")


async def notify_rating_request(user_id: str, username: str, content_id: str, content_name: str, content_type: str, watchlog_id: int):
    """
    Fonction appelée par le webhook pour demander une notation.
    Fait le pont entre FastAPI et le bot Discord.
    """
    global _bot_instance, _bot_loop
    
    if not _bot_instance or not _bot_loop:
        logger.error("❌ Giorgio bot not initialized!")
        return
    
    # Attend que le bot soit prêt
    retry_count = 0
    while not _bot_instance.is_ready() and retry_count < 10:
        await asyncio.sleep(0.5)
        retry_count += 1
    
    if not _bot_instance.is_ready():
        logger.error("❌ Giorgio bot not ready after 5 seconds")
        return
    
    # Schedule la coroutine dans la loop du bot
    future = asyncio.run_coroutine_threadsafe(
        _bot_instance.send_rating_request(user_id, username, content_id, content_name, content_type, watchlog_id),
        _bot_loop
    )
    
    try:
        future.result(timeout=10)  # Attend max 10 secondes
    except Exception as e:
        logger.error(f"❌ Failed to send rating request: {e}")