from unittest.mock import MagicMock

import MetaTrader5 as mt5
import pytest

from src.metatrader.order import place_order


@pytest.fixture
def mock_mt5(mocker):
    """
    Fixture to mock MetaTrader5 module methods.
    """
    mocker.patch.object(mt5, "symbol_info")
    mocker.patch.object(mt5, "account_info")
    mocker.patch.object(mt5, "symbol_info_tick")
    mocker.patch.object(mt5, "order_send")


def test_place_order_success_buy(mock_mt5):
    """
    Test successfully placing a BUY order.
    """
    # Mock symbol_info for USDCAD
    mt5.symbol_info.return_value = MagicMock(
        visible=True,
        point=0.00001,
        trade_tick_value=0.71682,
        volume_min=0.01,
        volume_step=0.01
    )

    # Mock account_info
    mt5.account_info.return_value = MagicMock(balance=1000.0)

    # Mock symbol_info_tick
    mt5.symbol_info_tick.return_value = MagicMock(ask=1.39629, bid=1.39674)

    # Mock order_send
    mt5.order_send.return_value = MagicMock(retcode=mt5.TRADE_RETCODE_DONE)

    # Call the function
    result = place_order(symbol="USDCAD", action="BUY", risk_per_trade=0.02, risk_in_pips=20, reward_to_risk_ratio=2)

    # Assert the results
    assert result is True, "The order should be placed successfully."

    mock_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "USDCAD",
        "volume": 0.14,
        "type": mt5.ORDER_TYPE_BUY,
        "price": 1.39629,
        "sl": 1.39429,
        "tp": 1.40029,
        "deviation": 10,  # Maximum allowed deviation in points
        "magic": 234000,  # Custom magic number
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    mt5.order_send.assert_called_once_with(mock_request)


def test_place_order_success_sell(mock_mt5):
    """
    Test successfully placing a BUY order.
    """
    # Mock symbol_info for USDCAD
    mt5.symbol_info.return_value = MagicMock(
        visible=True,
        point=0.00001,
        trade_tick_value=0.71682,
        volume_min=0.01,
        volume_step=0.01
    )

    # Mock account_info
    mt5.account_info.return_value = MagicMock(balance=1000.0)

    # Mock symbol_info_tick
    mt5.symbol_info_tick.return_value = MagicMock(ask=1.39629, bid=1.39674)

    # Mock order_send
    mt5.order_send.return_value = MagicMock(retcode=mt5.TRADE_RETCODE_DONE)

    # Call the function
    result = place_order(symbol="USDCAD", action="SELL", risk_per_trade=0.02, risk_in_pips=20, reward_to_risk_ratio=2)

    # Assert the results
    assert result is True, "The order should be placed successfully."

    mock_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "USDCAD",
        "volume": 0.14,
        "type": mt5.ORDER_TYPE_SELL,
        "price": 1.39674,
        "sl": 1.39874,
        "tp": 1.39274,
        "deviation": 10,  # Maximum allowed deviation in points
        "magic": 234000,  # Custom magic number
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    mt5.order_send.assert_called_once_with(mock_request)


def test_place_order_symbol_not_visible(mock_mt5):
    """
    Test placing an order when the symbol is not visible.
    """
    # Mock symbol_info for USDCAD (symbol not visible)
    mt5.symbol_info.return_value = MagicMock(visible=False)

    # Call the function
    result = place_order(symbol="USDCAD", action="BUY", risk_per_trade=0.02, risk_in_pips=20)

    # Assert the result
    assert result is False, "Order should fail because the symbol is not visible."
    mt5.order_send.assert_not_called()


def test_place_order_account_info_failure(mock_mt5):
    """
    Test placing an order when account info is unavailable.
    """
    # Mock symbol_info for USDCAD
    mt5.symbol_info.return_value = MagicMock(visible=True, point=0.00001, trade_tick_value=1.0)

    # Mock account_info to return None
    mt5.account_info.return_value = None

    # Call the function
    result = place_order(symbol="USDCAD", action="BUY", risk_per_trade=0.02, risk_in_pips=20)

    # Assert the result
    assert result is False, "Order should fail because account info is unavailable."
    mt5.order_send.assert_not_called()


def test_place_order_tick_data_failure(mock_mt5):
    """
    Test placing an order when tick data is unavailable.
    """
    # Mock symbol_info for USDCAD
    mt5.symbol_info.return_value = MagicMock(visible=True, point=0.00001, trade_tick_value=1.0)

    # Mock account_info
    mt5.account_info.return_value = MagicMock(balance=1000.0)

    # Mock symbol_info_tick to return None
    mt5.symbol_info_tick.return_value = None

    # Call the function
    result = place_order(symbol="USDCAD", action="BUY", risk_per_trade=0.02, risk_in_pips=20)

    # Assert the result
    assert result is False, "Order should fail because tick data is unavailable."
    mt5.order_send.assert_not_called()


def test_place_order_order_send_failed(mock_mt5):
    """
    Test placing an order with a failed order_send result.
    """
    # Mock symbol_info for USDCAD
    mt5.symbol_info.return_value = MagicMock(
        visible=True,
        point=0.00001,
        trade_tick_value=0.71682,
        volume_min=0.01,
        volume_step=0.01
    )

    # Mock account_info
    mt5.account_info.return_value = MagicMock(balance=1000.0)

    # Mock symbol_info_tick
    mt5.symbol_info_tick.return_value = MagicMock(ask=1.12345, bid=1.12300)

    # Mock order_send to fail
    mt5.order_send.return_value = MagicMock(retcode=mt5.TRADE_RETCODE_REJECT)

    # Call the function
    result = place_order(symbol="USDCAD", action="BUY", risk_per_trade=0.02, risk_in_pips=20)

    # Assert the result
    assert result is False, "Order should fail due to order_send failure."
    mt5.order_send.assert_called_once()


if __name__ == "__main__":
    pytest.main()
