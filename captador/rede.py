"""Download HTTPS limitado a destinos públicos; sem credenciais ou modelos de IA."""
import http.client
from html.parser import HTMLParser
import ipaddress
import socket
import ssl
import base64
from urllib.parse import urlsplit, urljoin, unquote
from urllib.request import getproxies, proxy_bypass

LIMITE = 15 * 1024 * 1024


def obter(url):
    if not isinstance(url, str) or len(url) > 2000:
        raise ValueError('URL inválida')
    historico = []
    for _ in range(6):
        u = urlsplit(url)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.port not in (None, 443):
            raise ValueError('Usar URL HTTPS pública sem credenciais e sem porta alternativa')
        ips = list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(u.hostname, 443, type=socket.SOCK_STREAM)))
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise ValueError('Destino de rede não público')

        class Conexao(http.client.HTTPSConnection):
            def connect(self):
                # Conecta ao IP já validado; não resolve o nome uma segunda vez.
                proxy = getproxies().get('https') if not proxy_bypass(self.host) else None
                if proxy:
                    p = urlsplit(proxy)
                    if p.scheme != 'http' or not p.hostname:
                        raise ValueError('Proxy HTTPS deve usar túnel CONNECT de um proxy HTTP confiável')
                    raw = socket.create_connection((p.hostname, p.port or 80), timeout=self.timeout)
                    headers = {}
                    if p.username is not None:
                        segredo = unquote(p.username)+':'+unquote(p.password or '')
                        headers['Proxy-Authorization'] = 'Basic '+base64.b64encode(segredo.encode()).decode()
                    # O proxy recebe o IP validado, mantendo TLS com o hostname original.
                    self.set_tunnel(ips[0], 443, headers=headers)
                    self.sock = raw
                    try:
                        self._tunnel()
                    except Exception:
                        raw.close()
                        raise
                else:
                    raw = None
                    for ip in ips:
                        try:
                            raw = socket.create_connection((ip, 443), timeout=self.timeout)
                            break
                        except OSError:
                            continue
                    if raw is None:
                        raise ValueError('Não foi possível conectar ao destino público')
                try:
                    self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=self.host)
                except Exception:
                    raw.close()
                    raise

        c = Conexao(u.hostname, timeout=30)
        try:
            caminho = u.path or '/'
            if u.query:
                caminho += '?' + u.query
            c.request('GET', caminho, headers={'Host': u.hostname, 'User-Agent': 'Mozilla/5.0 Captador/1.0', 'Accept-Encoding': 'identity'})
            r = c.getresponse()
            historico.append({'url': url, 'http': r.status})
            if r.status in (301, 302, 303, 307, 308):
                destino = r.getheader('Location')
                if not destino:
                    raise ValueError('Redirecionamento sem destino')
                url = urljoin(url, destino)
                continue
            if r.status != 200:
                raise ValueError(f'Download recusado: HTTP {r.status}')
            if int(r.getheader('Content-Length', '0')) > LIMITE:
                raise ValueError('Arquivo excede 15 MiB')
            corpo = r.read(LIMITE + 1)
            if not corpo or len(corpo) > LIMITE:
                raise ValueError('Resposta vazia ou acima de 15 MiB')
            return corpo, {'url_final': url, 'redirecionamentos': historico,
                           'content_type': r.getheader('Content-Type', '')}
        finally:
            c.close()
    raise ValueError('Limite de redirecionamentos excedido')


class Listagem(HTMLParser):
    def __init__(self, url):
        super().__init__()
        self.url, self.itens, self.item, self.heading, self.link = url, [], None, None, None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h2':
            self.heading = []
            self.item = {'titulo': '', 'prova_url': '', 'gabarito_url': ''}
            self.itens.append(self.item)
        if tag == 'a':
            self.link = {'href': attrs.get('href', ''), 'texto': []}

    def handle_data(self, data):
        if self.heading is not None:
            self.heading.append(data)
        if self.link is not None:
            self.link['texto'].append(data)

    def handle_endtag(self, tag):
        if tag == 'h2' and self.heading is not None:
            self.item['titulo'] = ' '.join(' '.join(self.heading).split())
            self.heading = None
        if tag == 'a' and self.link:
            texto = ' '.join(self.link['texto']).casefold()
            href = urljoin(self.url, self.link['href'])
            if self.item and texto.strip().startswith('baixar prova'):
                self.item['prova_url'] = href
            if self.item and texto.strip().startswith('baixar gabarito'):
                self.item['gabarito_url'] = href
            self.link = None


def descobrir(url):
    raw, origem = obter(url)
    if raw.startswith(b'%PDF-'):
        return {'pdf_direto': True, 'url': url, 'origem': origem, 'candidatos': []}
    if 'html' not in origem['content_type'].lower():
        raise ValueError('A URL não retornou página HTML nem PDF')
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Página acima de 2 MiB')
    parser = Listagem(origem['url_final'])
    parser.feed(raw.decode('utf-8', errors='replace'))
    itens = [i for i in parser.itens if i['prova_url'] or i['gabarito_url']]
    return {'pdf_direto': False, 'origem': origem, 'candidatos': itens,
            'aviso': 'Selecione e confira prova/caderno; nenhuma associação ou identidade é presumida.'}
