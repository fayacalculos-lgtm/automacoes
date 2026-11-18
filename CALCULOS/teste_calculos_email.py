"""Testes offline do CALCULOS/main.py (sem Gmail): python CALCULOS/teste_calculos_email.py"""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as c  # noqa: E402


class TestOK(unittest.TestCase):
    def test_ok_aprova(self):
        for t in ['OK', 'ok', 'Ok.', 'OK pode enviar', '\n\n  OK\n\nEm ter., 18 de nov. de 2026 escreveu:\n> resumo']:
            self.assertTrue(c.eh_ok(t), t)

    def test_nao_aprova(self):
        for t in ['Não envie ainda', 'okay', 'Revisar o ok depois', '', '> OK (citado)',
                  'Em ter., 18 de nov. de 2026, Faya escreveu:\n> OK']:
            self.assertFalse(c.eh_ok(t), t)

    def test_primeira_linha_ignora_citacao(self):
        self.assertEqual(c.primeira_linha_util('\nOn Tue, Nov 18 wrote:\n> OK'), '')


class TestRegras(unittest.TestCase):
    def test_pendencias(self):
        p = c.pendencias('Valor: [CONFERIR: valor do software] {{NOME_AUTOR}} [NARRAR: fatos]')
        self.assertEqual(len(p), 3)
        self.assertEqual(c.pendencias('Segue cálculo. Fico à disposição.'), [])

    def test_consulta_exclui_proprios_e_exige_anexo(self):
        q = c.consulta(3)
        self.assertIn('newer_than:3d', q)
        self.assertIn('has:attachment', q)
        self.assertIn('-from:me', q)

    def test_nome_pasta_limpa_caracteres(self):
        n = c.nome_pasta('2026-11-18', 'Dra. Edith', 'Re: CÁLCULO / PRAZO: 11/11?')
        self.assertNotRegex(n, r'[<>:"/\\|?*]')
        self.assertTrue(n.startswith('2026-11-18 - Dra. Edith - '))

    def test_texto_arquivo_md(self):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write('x [CONFERIR: y]')
        try:
            self.assertEqual(c.pendencias(c.texto_arquivo(f.name)), ['[CONFERIR: y]'])
        finally:
            os.unlink(f.name)


class TestEstadoESemEnvio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(c, 'pasta_saida', return_value=self.tmp)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_aprovacoes_sem_pedido_preparado_nao_abre_gmail(self):
        c.salvar_estado({'a': {'status': 'novo'}, 'b': {'status': 'enviado'}})
        with mock.patch.object(c, '_svc_envio') as svc:
            c.cmd_aprovacoes(None)
        svc.assert_not_called()

    def test_aprovacoes_sem_ok_nao_envia(self):
        c.salvar_estado({'x': {'status': 'preparado', 'resumo_thread': 't', 'resumo_id': 'r1', 'draft_id': 'd'}})
        fake = mock.MagicMock()
        fake.users().threads().get().execute.return_value = {'messages': [
            {'id': 'r1', 'snippet': 'OK resumo do sistema'},
            {'id': 'm2', 'payload': {'mimeType': 'text/plain', 'body': {'data': 'TsOjbyBlbnZpZQ=='}}}]}  # "Não envie"
        with mock.patch.object(c, '_svc_envio', return_value=fake):
            c.cmd_aprovacoes(None)
        fake.users().drafts().send.assert_not_called()
        self.assertEqual(c.ler_estado()['x']['status'], 'preparado')

    def test_aprovacoes_com_ok_envia_uma_vez(self):
        c.salvar_estado({'x': {'status': 'preparado', 'resumo_thread': 't', 'resumo_id': 'r1', 'draft_id': 'd',
                               'de': 'p@x', 'assunto': 'A', 'pasta': 'P'}})
        fake = mock.MagicMock()
        fake.users().threads().get().execute.return_value = {'messages': [
            {'id': 'r1', 'snippet': 'resumo'},
            {'id': 'm2', 'payload': {'mimeType': 'text/plain', 'body': {'data': 'T0sgcG9kZSBlbnZpYXI='}}}]}  # "OK pode enviar"
        fake.users().drafts().send().execute.return_value = {'id': 'env1'}
        with mock.patch.object(c, '_svc_envio', return_value=fake), mock.patch.object(c, '_fluxo_rt', return_value='n'):
            c.cmd_aprovacoes(None)
            self.assertEqual(c.ler_estado()['x']['status'], 'enviado')
            fake.users().drafts().send.reset_mock()
            c.cmd_aprovacoes(None)   # 2a rodada: ja enviado, nao manda de novo
        fake.users().drafts().send.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=1)
