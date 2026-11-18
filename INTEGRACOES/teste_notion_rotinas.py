"""Testes offline das rotinas que gravam no Notion: python INTEGRACOES/teste_notion_rotinas.py"""
import os
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in ('', 'NUCLEO', 'INTEGRACOES'):
    sys.path.insert(0, os.path.join(RAIZ, p))
import notion_escritorio as ne  # noqa: E402

# FINANCEIRO e CONTROLADORIA tem cada um o seu comum.py: carrega um de cada vez
sys.path.insert(0, os.path.join(RAIZ, 'FINANCEIRO'))
import notion_financeiro as nf  # noqa: E402
sys.path.remove(os.path.join(RAIZ, 'FINANCEIRO'))
sys.modules.pop('comum', None)
sys.path.insert(0, os.path.join(RAIZ, 'CONTROLADORIA'))
import notion_prazos as npz  # noqa: E402


def pag(i, cust='c1', valor=100.0, pago=None, venc='2026-11-10', **kw):
    d = {'id': i, 'customer': cust, 'value': valor, 'dueDate': venc, 'paymentDate': pago, 'description': 'Honorários',
         'billingType': 'PIX'}
    d.update(kw)
    return d


class TestFinanceiro(unittest.TestCase):
    def test_recebido_sem_registro_cria_pago(self):
        a = nf.planejar([], [pag('p1', pago='2026-11-15')], {}, {'c1': 'MARIA SILVA'}, [])
        self.assertEqual(a[0]['acao'], 'criar')
        self.assertTrue(a[0]['pago'])

    def test_recebido_de_linha_do_sistema_marca_pago(self):
        reg = {'p1': {'notion_id': 'n1', 'pago': False}}
        a = nf.planejar([], [pag('p1', pago='2026-11-15')], reg, {'c1': 'MARIA'}, [])
        self.assertEqual(a[0]['acao'], 'marcar_pago')
        self.assertEqual(a[0]['notion_id'], 'n1')

    def test_ja_pago_pula(self):
        reg = {'p1': {'notion_id': 'n1', 'pago': True}}
        self.assertEqual(nf.planejar([], [pag('p1', pago='2026-11-15')], reg, {}, [])[0]['acao'], 'pular')

    def test_emitida_cria_em_aberto_e_nao_repete_recebida(self):
        a = nf.planejar([pag('p2'), pag('p1')], [pag('p1', pago='2026-11-15')], {}, {'c1': 'X'}, [])
        self.assertEqual([x['p']['id'] for x in a], ['p1', 'p2'])
        self.assertFalse(a[1]['pago'])

    def test_duplicata_de_lancamento_manual_e_pulada(self):
        manual = [{'titulo': 'Maria Silva', 'valor': '100.0', 'data_pagamento': '2026-11-14'}]
        a = nf.planejar([], [pag('p1', pago='2026-11-15')], {}, {'c1': 'MARIA SILVA'}, manual)
        self.assertEqual(a[0]['acao'], 'pular')
        self.assertIn('à mão', a[0]['motivo'])

    def test_valor_diferente_nao_e_duplicata(self):
        manual = [{'titulo': 'Maria Silva', 'valor': '250', 'data_pagamento': '2026-11-15'}]
        self.assertIsNone(nf.parece_duplicata('MARIA SILVA', 100, '2026-11-15', manual))

    def test_valores_nao_adivinha_classificacao(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('NOTION_FIN_CLASSIFICACAO', None)
            v = nf.valores(pag('p1', pago='2026-11-15'), 'X', True)
        self.assertIsNone(v['classificacao'])
        self.assertIn('ASAAS#p1', v['texto'])
        self.assertEqual(v['data_pagamento'], '2026-11-15')


class TestAtualizarPropria(unittest.TestCase):
    ESQ = {'Texto': {'type': 'rich_text'}, 'Pago': {'type': 'checkbox'}, 'Data do pagamento': {'type': 'date'}}

    def _pagina(self, texto):
        return {'properties': {'Texto': {'type': 'rich_text', 'rich_text': [{'plain_text': texto}]}}}

    def test_recusa_linha_sem_marcador(self):
        with mock.patch.object(ne.ni, '_request', return_value=self._pagina('lançado pela Bárbara')), \
                mock.patch.object(ne.ni, 'atualizar_pagina') as up:
            r = ne.atualizar_propria('financeiro', 'x', {'pago': True}, 'ASAAS#p1', esq=self.ESQ)
        up.assert_not_called()
        self.assertFalse(r['gravado'])

    def test_atualiza_linha_do_sistema(self):
        with mock.patch.object(ne.ni, '_request', return_value=self._pagina('ASAAS#p1 | Honorários')), \
                mock.patch.object(ne.ni, 'atualizar_pagina') as up:
            r = ne.atualizar_propria('financeiro', 'x', {'pago': True, 'data_pagamento': '2026-11-15'}, 'ASAAS#p1',
                                     esq=self.ESQ)
        up.assert_called_once()
        self.assertEqual(up.call_args[0][1]['Pago'], {'checkbox': True})
        self.assertTrue(r['gravado'])


class TestPrazos(unittest.TestCase):
    def item(self, **kw):
        i = {'prazo_nosso': 'SIM', 'categoria': 'SENTENCA', 'interno_iso': '2026-11-23', 'evento_data': '',
             'gravidade': 'ALTA', 'cliente': 'JOAO', 'tribunal': 'TRF1', 'id_djen': 9, 'fatal': '26/11/2026',
             'processo': '0000000-00.2026.4.01.0000', 'rotulo': 'Sentença'}
        i.update(kw)
        return i

    def test_candidatos(self):
        itens = [self.item(), self.item(prazo_nosso='NÃO'), self.item(categoria='DESPACHO'),
                 self.item(interno_iso='', evento_data='')]
        self.assertEqual(len(npz.candidatos(itens)), 1)

    def test_valores_da_linha(self):
        os.environ.pop('NOTION_CONTRATANTE_PADRAO', None)
        v = npz.valores(self.item(), 'DJEN#9 | Sentença')
        self.assertEqual(v['titulo'], 'Particular')
        self.assertEqual(v['data'], '2026-11-23')
        self.assertEqual(v['status'], 'PRAZO')
        self.assertEqual(v['prioridade'], 'Alta')

    def test_tribunal_que_nao_existe_e_ignorado(self):
        esq = {'Contratante': {'type': 'title'}, 'Tribunal': {'type': 'select', 'opcoes': ['TJSP']},
               'Status': {'type': 'status', 'opcoes': ['PRAZO']}}
        props, avisos = ne.montar_propriedades('prazos', npz.valores(self.item(), 'x'), esq)
        self.assertNotIn('Tribunal', props)
        self.assertTrue(any('TRF1' in a for a in avisos))

    def test_simulacao_nao_grava(self):
        with mock.patch.object(ne.ni, 'criar_pagina') as cp:
            npz.enviar([self.item()], lambda i: 'x', gravar=False)
        cp.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=1)
