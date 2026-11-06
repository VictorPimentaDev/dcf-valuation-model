"""Reconcile the research snapshot to the selected, attributed CVM rows."""

from importlib.resources import files

import pandas as pd
import pytest

from dcf_valuation.model import load_data


def test_ttm_and_balance_bridge_reconcile_to_cvm():
    data = load_data()
    rows = pd.read_csv(files('dcf_valuation').joinpath('data/cvm_weg.csv'), dtype=str)

    def amount(prefix, code, period):
        selected = rows[
            rows['file'].str.startswith(prefix)
            & (rows['CD_CONTA'] == code)
            & (rows['DT_FIM_EXERC'] == period)
        ]
        assert len(selected) == 1
        assert selected.iloc[0]['ESCALA_MOEDA'] == 'MIL'
        return float(selected.iloc[0]['VL_CONTA']) / 1000

    def ttm(table, code):
        return (
            amount(f'dfp_cia_aberta_{table}', code, '2025-12-31')
            + amount(f'itr_cia_aberta_{table}', code, '2026-09-30')
            - amount(f'itr_cia_aberta_{table}', code, '2025-09-30')
        )

    historical = data['historical'][-1]
    assert historical['revenue'] == pytest.approx(ttm('DRE', '3.01'))
    assert historical['da'] == pytest.approx(ttm('DFC_MI', '6.01.01.02'))
    assert historical['ebitda'] == pytest.approx(ttm('DRE', '3.05') + historical['da'])
    a = data['assumptions']
    def current(table, code):
        return amount(f'itr_cia_aberta_{table}', code, '2026-09-30')

    assert a['cash'] == pytest.approx(current('BPA', '1.01.01') + current('BPA', '1.01.02'))
    assert a['debt'] == pytest.approx(current('BPP', '2.01.04') + current('BPP', '2.02.01'))
    assert a['other_claims'] == pytest.approx(sum(current('BPP', code) for code in (
        '2.01.05.02.07', '2.02.02.02.05', '2.03.09',
    )))
    import json

    capital = json.loads(files('dcf_valuation').joinpath('data/capital_weg.json').read_text())
    assert a['shares'] == pytest.approx((
        int(capital['QT_ACAO_TOTAL_CAP_INTEGR']) - int(capital['QT_ACAO_TOTAL_TESOURO'])
    ) / 1_000_000)
