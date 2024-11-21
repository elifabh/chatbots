# src/web_search.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

class WebSearch:
    def __init__(self, website_url):
        self.website_url = website_url.rstrip('/')
    
    def search(self, query):
        try:
            # Şirketin web sitesindeki arama URL'sini oluşturun
            search_url = f"{self.website_url}/search?q={quote(query)}"
            response = requests.get(search_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Arama sonuçlarının bulunduğu HTML yapısına göre düzenleyin
                # Örneğin, arama sonuçları 'div' etiketi içinde 'search-result' sınıfında olabilir
                for item in soup.find_all('div', class_='search-result'):
                    title_tag = item.find('h2')
                    snippet_tag = item.find('p')
                    link_tag = item.find('a', href=True)
                    
                    if title_tag and snippet_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        snippet = snippet_tag.get_text(strip=True)
                        link = link_tag['href']
                        
                        # Bağlantı tam değilse tamamlayın
                        if not link.startswith('http'):
                            link = self.website_url + '/' + link.lstrip('/')
                        
                        results.append(f"{title}\n{snippet}\n{link}")
                
                return results
            else:
                print(f"Web arama hatası: Status Code {response.status_code}")
                return []
        except Exception as e:
            print(f"Web arama hatası: {e}")
            return []