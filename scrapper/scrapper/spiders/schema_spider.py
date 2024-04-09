import scrapy, time, re, csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from imdbscrapper.items import ImdbscrapperItem
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from scrapy.http import HtmlResponse

class BygenreSpider(scrapy.Spider):
    name = "bygenre"
    allowed_domains = ["www.imdb.com"]
    #start_urls = ["https://www.imdb.com/feature/genre/?ref_=nv_ch_gr"]
    #start_urls = ["https://www.imdb.com/search/title/?title_type=feature"]
    
    def __init__(self):
       
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")  # Utiliser le disque au lieu de /dev/shm pour le stockage temporaire
        chrome_options.add_argument("--no-sandbox")  # Désactiver le mode sandbox pour Chrome
        chrome_options.add_argument("--disable-gpu")  # Désactiver l'accélération matérielle

        chrome_service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    
    
    def start_requests(self):
        # Emplacement de votre fichier CSV
        csv_file_path = 'parse_detail_page.csv'
        # Lire les IDs de film à partir du fichier CSV
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                film_id = row['film_id']
                url = f'https://www.imdb.com/title/{film_id}/releaseinfo/?ref_=tt_dt_rdat'
                item = ImdbscrapperItem()
                item['film_id'] = film_id
                yield scrapy.Request(url, callback=self.parse_date_sortie, meta={'item': item})
    
    def parse_date_sortie(self, response):
        item = response.meta['item']
        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 5)

        # Handle cookie acceptance
        try:
            accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Accept")]')))
            accept_button.click()
        except (NoSuchElementException, TimeoutException):
            self.logger.info("Accept button not found or not clickable.")
        
        try:
            while True:
                # Attente pour que le bouton soit cliquable
                button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '/html/body/div[2]/main/div/section/div/section/div/div[1]/section[1]/div[2]/ul/div/span[1]/button')))
                
                # Amélioration du défilement pour s'assurer que le bouton est dans une position cliquable
                
                self.driver.execute_script("arguments[0].click();", button)
        except TimeoutException:
            self.logger.info("Plus de boutons 'Voir plus' à cliquer.")


        # Extract the release date using Selenium
        try:
            france_release_date_element = self.driver.find_element(By.XPATH, "//a[@aria-label='France']/following-sibling::div/ul/li/span[@class='ipc-metadata-list-item__list-content-item']")
            france_release_date = france_release_date_element.text
        except NoSuchElementException:
            france_release_date = "No date found"
            self.logger.info("Release date in France not found.")

        item['date_sortie'] = france_release_date
        

        self.logger.info(f"Release date in France: {france_release_date}")
        yield item
        

    '''def parse(self, response):
        self.logger.info(f'Parsing genre page: {response.url}')
        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 3)

        try:
            accept_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Accept")]'))
            )
            accept_button.click()
        except (NoSuchElementException, TimeoutException):
            self.logger.info("Bouton d'acceptation des cookies non trouvé ou non cliquable.")
        click_count = 0
        try:
            while click_count < 50:
                # Attente pour que le bouton soit cliquable
                button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[2]/div/span/button')))
                
                # Amélioration du défilement pour s'assurer que le bouton est dans une position cliquable
                self.driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -150);", button)
                #time.sleep(1)  # Petite pause pour permettre à la page de s'ajuster après le défilement
                
                # Utilisation de JavaScript pour forcer le clic sur le bouton
                self.driver.execute_script("arguments[0].click();", button)
                click_count += 1 
                # Attente pour s'assurer que le contenu supplémentaire est bien chargé avant de continuer
                #time.sleep(2)  # Ajustez ce délai selon la vitesse de chargement de votre page

        except TimeoutException:
            self.logger.info("Plus aucun bouton 'voir plus' à cliquer ou fin de la pagination.")
        except Exception as e:
            self.logger.error(f"Une erreur est survenue lors de l'interaction avec le bouton 'voir plus': {e}")

        # Remontez en haut de la page une fois tous les films chargés
        self.driver.execute_script("window.scrollTo(0, 0);")



        # Extraction des URLs de détail des films. La correction suppose que l'extraction doit se faire avec Selenium
        detail_urls = set([a.get_attribute('href') for a in self.driver.find_elements(By.XPATH, "//a[contains(@class, 'ipc-lockup-overlay')]")])

        for url in detail_urls:
            self.logger.debug(f'Detail page URL found: {url}')
            yield scrapy.Request(url, callback=self.parse_detail_page)
            
                



    def parse_detail_page(self, response):
        self.logger.info(f'Parsing detail page: {response.url}')
        item = ImdbscrapperItem()
        
        # Extraction du titre du film
        item['titre'] = response.xpath("//h1[@data-testid='hero__pageTitle']/span/text()").get() or 'Titre non trouvé'

        # Extraction des autres informations à partir des XPath correspondants
        item['score'] = response.xpath('//div[contains(@data-testid, "hero-rating-bar__aggregate-rating__score")]/span/text()').get() or "0"
        item['nbre_vote'] = response.xpath('//div[@data-testid="hero-rating-bar__aggregate-rating__score"]/following-sibling::div[2]/text()').get() or "0"
        item['genres'] = response.xpath('//div[@data-testid="genres"]//div//a/span/text()').getall() or ["No kind"]
        item['langue'] = response.xpath('//li[contains(@data-testid, "title-details-languages")]//a/text()').getall() or ["No Language"]
        item['pays'] = response.xpath('//li[contains(@data-testid, "title-details-origin")]//a/text()').getall() or ["No Country"]
        item['pegi'] = response.xpath('//h1/following-sibling::ul[1]/li[2]//text()').get() or "No Pegi"
        item['duree'] = response.xpath('//h1/following-sibling::ul[1]/li[3]//text()').get() or "0"
        item['annee'] = response.xpath('//h1/following-sibling::ul[1]/li[1]//text()').get() or "0"
        item['popularite_score'] = response.xpath('//div[@data-testid="hero-rating-bar__popularity__score"]/text()').get() or ["No Popularity Score"]
        item['director'] = response.xpath('//li[@data-testid="title-pc-principal-credit"]//a/text()').get() or ["No Director"]
        item['scenaristes'] = response.xpath('//li[@data-testid="title-pc-principal-credit"]//a/text()').get() or ["No Writers"]
        item['casting_principal'] = response.xpath('//li[@data-testid="title-pc-principal-credit"]//a/text()').getall()[:3] or ["No Casting"]
        item['casting_complet'] = response.xpath('//div[@data-testid="title-cast-item"]//a[@data-testid="title-cast-item__actor"]/text()').extract() or ["No Casting"]
        item['budget'] = response.xpath('//li[@data-testid="title-boxoffice-budget"]//div//span/text()').get() or ["No budget"]
        film_url = response.url
        # Utilisez re.search pour trouver l'ID du film dans l'URL
        film_id_search = re.search(r'tt\d+', film_url)
        if film_id_search:
            item['film_id'] = film_id_search.group()  # Cela extrait la correspondance de l'expression régulière
        else:
            item['film_id'] = 'ID non trouvé'
        yield item

        # Extraction de l'URL du lien "Date de sortie"
        date_sortie_link = response.xpath("//li[@data-testid='title-details-releasedate']/a/@href").get()
        also_know_as_link = response.xpath("//li[@data-testid='title-details-akas']/a/@href").get()

        if date_sortie_link:
            request = scrapy.Request(response.urljoin(date_sortie_link), callback=self.parse_date_sortie, meta={'item': item})
            request.meta['also_know_as_link'] = also_know_as_link  # Stockez l'URL AKA pour l'utiliser plus tard
            yield request
        elif also_know_as_link:  # Si la date de sortie n'est pas nécessaire ou absente
            yield scrapy.Request(response.urljoin(also_know_as_link), callback=self.parse_know_as, meta={'item': item})
        else:
            yield item'''
 


    

    '''# Vérifiez si le lien AKA doit être suivi
        also_know_as_link = response.meta.get('also_know_as_link')
        if also_know_as_link:
            yield scrapy.Request(response.urljoin(also_know_as_link), callback=self.parse_know_as, meta={'item': item})
        else:'''
        



    '''def parse_know_as(self,response):
        item = response.meta['item']

        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 5)

        # Accepte les cookies
        try:
            accept_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Accept")]'))
            )
            accept_button.click()
        except (NoSuchElementException, TimeoutException):
            self.logger.info("Bouton d'acceptation des cookies non trouvé ou non cliquable.")

        # Click all "more" or "All" buttons to reveal hidden content
        try:
            # Boucle pour cliquer sur le bouton "Voir plus" tant qu'il est présent
            while True:
                # Utilisation de WebDriverWait pour attendre que le bouton soit cliquable
                button = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, '/html/body/div[2]/main/div/section/div/section/div/div[1]/section[1]/div[2]/ul/div/span[1]/button')))
                    
                # Amélioration du défilement pour s'assurer que le bouton est dans une position cliquable
                self.driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -150);", button)
                
                
                # Utilisation de JavaScript pour forcer le clic sur le bouton
                self.driver.execute_script("arguments[0].click();", button)
                    
                    
                    
        except TimeoutException:
            self.logger.info("Aucun bouton 'voir plus' ou 'Tout' trouvé ou fin de la pagination.")

        # Find and extract the France release date
        france_know_as = "Pas de titre français"  # Initialise avec une valeur par défaut
        try:
            know_as_france =wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//a[@aria-label='France']/following-sibling::div/ul/li/span[@class='ipc-metadata-list-item__list-content-item']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", know_as_france)

            self.driver.execute_script("arguments[0].scrollIntoView(true);", know_as_france)
            france_know_as = know_as_france.text
        except (NoSuchElementException, TimeoutException):
            self.logger.error(f"Le titre  pour la France n'a pas été trouvée ou a expiré. {response.url}")

        self.logger.info(f"titre  en France: {france_know_as}")

        # Création et retour de l'item avec toutes les données récupérées jusqu'à maintenant
        item['titre_france'] = france_know_as
        
        yield item'''


    def close(self, reason):
        self.driver.quit()
        super(BygenreSpider, self).close(self, reason)