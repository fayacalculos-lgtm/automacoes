"""Testes offline do notion_escritorio (sem rede, sem token): python INTEGRACOES/teste_notion_escritorio.py"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notion_escritorio as ne  # noqa: E402

ESQ_PRAZOS = {
    'Contratante': {'type': 'title'}, 'Cliente': {'type': 'rich_text'}, 'Texto': {'type': 'rich_text'},
    'Data': {'type': 'date'}, 'Responsável': {'type': 'people'},
    'Status': {'type': 'status', 'opcoes': ['PRAZO', 'Não iniciada', 'Em andamento', 'Concluído']},
    'Tribunal': {'type': 'select', 'opcoes': ['TJSP', 'TRT 3']},
    'Fluxo RT': {'type': 'select', 'opcoes': ['PRAZO', 'CÁLCULO']},
}
ESQ_FIN = {
    'Cliente': {'type': 'title'}, 'Valor': {'type': 'number'}, 'Pago': {'type': 'checkbox'},
    'Tipo': {'type': 'select', 'opcoes': ['Entrada', 'Saída']},
    'Área': {'type': 'select', 'opcoes': ['Previdenciário', 'Cível']},
    'Contratante': {'type': 'relation'}, 'Valor Parcela': {'type': 'formula'},
}


class TestMontar(unittest.TestCase):
    def test_tarefa_tipos(self):
        p, av = ne.montar_propriedades('prazos', {
            'titulo': '[TESTE] apagar', 'cliente': 'X', 'data': '2026-12-01', 'status': 'PRAZO', 'etapa': 'CÁLCULO'},
            ESQ_PRAZOS)
        self.assertEqual(p['Contratante']['title'][0]['text']['content'], '[TESTE] apagar')
        self.assertEqual(p['Data'], {'date': {'start': '2026-12-01'}})
        self.assertEqual(p['Status'], {'status': {'name': 'PRAZO'}})
        self.assertEqual(p['Fluxo RT'], {'select': {'name': 'CÁLCULO'}})
        self.assertEqual(av, [])

    def test_opcao_inexistente_nao_cria(self):
        p, av = ne.montar_propriedades('prazos', {'titulo': 'T', 'tribunal': 'TRF1', 'status': 'Inventado'}, ESQ_PRAZOS)
        self.assertNotIn('Tribunal', p)
        self.assertNotIn('Status', p)
        self.assertEqual(len(av), 2)

    def test_coluna_ausente_e_formula_ignoradas(self):
        p, av = ne.montar_propriedades('financeiro', {'titulo': 'C', 'classificacao': 'Honorários'}, ESQ_FIN)
        self.assertNotIn('Classificação', p)
        self.assertTrue(any('nao existe' in a for a in av))
        p, av = ne.montar_propriedades('financeiro', {'titulo': 'C'}, dict(ESQ_FIN, Cliente={'type': 'formula'}))
        self.assertEqual(p, {})

    def test_financeiro(self):
        p, _ = ne.montar_propriedades('financeiro', {'titulo': 'C', 'valor': 1500, 'pago': True, 'tipo': 'Entrada',
                                                     'area': 'Previdenciário', 'contratante': 'abc'}, ESQ_FIN)
        self.assertEqual(p['Valor'], {'number': 1500.0})
        self.assertEqual(p['Pago'], {'checkbox': True})
        self.assertEqual(p['Contratante'], {'relation': [{'id': 'abc'}]})

    def test_vazio_e_texto_longo(self):
        p, _ = ne.montar_propriedades('prazos', {'titulo': 'T', 'texto': 'a' * 4000, 'cliente': ''}, ESQ_PRAZOS)
        self.assertNotIn('Cliente', p)
        self.assertEqual(len(p['Texto']['rich_text']), 3)


class TestCriar(unittest.TestCase):
    def test_sem_gravar_nao_escreve(self):
        with mock.patch.object(ne.ni, 'criar_pagina') as cp:
            r = ne.criar('prazos', {'titulo': 'T'}, gravar=False, esq=ESQ_PRAZOS)
        cp.assert_not_called()
        self.assertFalse(r['gravado'])

    def test_gravar_cria_uma_pagina(self):
        with mock.patch.object(ne.ni, 'criar_pagina', return_value={'id': 'p1', 'url': 'u'}) as cp:
            r = ne.criar('prazos', {'titulo': 'T'}, gravar=True, esq=ESQ_PRAZOS)
        cp.assert_called_once()
        self.assertEqual(cp.call_args[0][0], ne.BASES['prazos'])
        self.assertTrue(r['gravado'])

    def test_nunca_atualiza_nem_apaga(self):
        with mock.patch.object(ne.ni, 'atualizar_pagina') as up, mock.patch.object(ne.ni, 'criar_pagina', return_value={}):
            ne.criar('prazos', {'titulo': 'T'}, gravar=True, esq=ESQ_PRAZOS)
        up.assert_not_called()

    def test_base_desconhecida(self):
        with self.assertRaises(SystemExit):
            ne.base_id('nao-existe')


class TestLeitura(unittest.TestCase):
    def test_listar_traduz_colunas(self):
        pagina = {'id': 'x', 'properties': {
            'Contratante': {'type': 'title', 'title': [{'plain_text': 'Fulano'}]},
            'Data': {'type': 'date', 'date': {'start': '2026-12-01'}},
            'Status': {'type': 'status', 'status': {'name': 'PRAZO'}},
            'Outra': {'type': 'rich_text', 'rich_text': []}}}
        with mock.patch.object(ne.ni, 'consultar_banco', return_value=[pagina]):
            r = ne.listar('prazos', 5)
        self.assertEqual(r[0]['titulo'], 'Fulano')
        self.assertEqual(r[0]['data'], '2026-12-01')
        self.assertEqual(r[0]['status'], 'PRAZO')
        self.assertNotIn('Outra', r[0])

    def test_achar_cliente_so_se_unico(self):
        with mock.patch.object(ne.ni, 'consultar_banco', return_value=[{'id': 'a'}]):
            self.assertEqual(ne.achar_cliente('X'), 'a')
        with mock.patch.object(ne.ni, 'consultar_banco', return_value=[{'id': 'a'}, {'id': 'b'}]):
            self.assertIsNone(ne.achar_cliente('X'))


if __name__ == '__main__':
    unittest.main(verbosity=1)
