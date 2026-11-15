import importlib.util
from pathlib import Path
import unittest
import io
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('rede',Path(__file__).resolve().parents[1]/'rede.py')
rede=importlib.util.module_from_spec(spec);spec.loader.exec_module(rede)


class RedeTest(unittest.TestCase):
    def test_proxy_preserva_ip_validado_e_hostname_tls(self):
        class Sock:
            def __init__(self):
                self.envios=[]
                self.respostas=[b'HTTP/1.0 200 Connection established\r\n\r\n',
                                b'HTTP/1.1 200 OK\r\nContent-Length: 9\r\nContent-Type: application/pdf\r\n\r\n%PDF-1.4\n']
            def sendall(self,d):self.envios.append(d)
            def makefile(self,*args):return io.BytesIO(self.respostas.pop(0))
            def close(self):pass
        sock=Sock()
        with patch.object(rede.socket,'getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]), \
             patch.object(rede.socket,'create_connection',return_value=sock), \
             patch.object(rede,'getproxies',return_value={'https':'http://proxy.test:8080'}), \
             patch.object(rede,'proxy_bypass',return_value=False), \
             patch.object(rede.ssl,'create_default_context') as ssl:
            ssl.return_value.wrap_socket.return_value=sock
            raw,info=rede.obter('https://public.example/prova.pdf')
            self.assertEqual(raw,b'%PDF-1.4\n')
            self.assertIn(b'CONNECT 8.8.8.8:443',sock.envios[0])
            self.assertIn(b'Host: public.example',sock.envios[1])
            ssl.return_value.wrap_socket.assert_called_once_with(sock,server_hostname='public.example')

    def test_esquemas_recusados(self):
        for url in ('file:///etc/passwd','http://example.org/a','https://u:p@example.org/a','https://example.org:8443/a'):
            with self.subTest(url=url),self.assertRaises(ValueError):rede.obter(url)

    def test_redes_privadas_recusadas(self):
        for ip in ('127.0.0.1','10.0.0.1','169.254.169.254','::1'):
            with patch.object(rede.socket,'getaddrinfo',return_value=[(2,1,6,'',(ip,443))]):
                with self.assertRaises(ValueError):rede.obter('https://example.org/a')

    def test_associacao_de_links_por_cartao(self):
        p=rede.Listagem('https://example.org/provas')
        p.feed('<h2><a>Prova A</a></h2><a href="/a.pdf">Baixar Prova</a><a href="/g.pdf">Baixar Gabarito</a><h2>Prova B</h2><a href="/b.pdf">Baixar Prova</a>')
        self.assertEqual(len(p.itens),2)
        self.assertEqual(p.itens[0]['gabarito_url'],'https://example.org/g.pdf')
        self.assertEqual(p.itens[1]['gabarito_url'],'')


if __name__=='__main__':unittest.main()
