# graphs.py
import plotly.graph_objects as go
import pandas as pd

def plot_price_chart(data: pd.DataFrame, trade_history: pd.DataFrame):
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Price'
    )])

    # Add entry markers
    entries = trade_history.dropna(subset=['entry_date'])
    fig.add_trace(go.Scatter(
        x=entries['entry_date'],
        y=entries['entry_price'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'
    ))

    # Add exit markers
    exits = trade_history.dropna(subset=['exit_date'])
    fig.add_trace(go.Scatter(
        x=exits['exit_date'],
        y=exits['exit_price'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'
    ))

    fig.update_layout(title='Price Chart with Trade Signals', xaxis_title='Date', yaxis_title='Price')
    fig.show()

def plot_equity_curve(equity_curve: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_curve['date'],
        y=equity_curve['equity'],
        mode='lines',
        name='Equity Curve'
    ))

    fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Account Balance')
    fig.show()

def plot_price_chart_with_equity(data: pd.DataFrame, trade_history: pd.DataFrame, equity_curve: pd.DataFrame):
    fig = go.Figure()

    # Add asset price line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['close'],
        mode='lines',
        name='Asset Price',
        line=dict(color='blue')
    ))

    # Add entry markers
    entries = trade_history.dropna(subset=['entry_date'])
    fig.add_trace(go.Scatter(
        x=entries['entry_date'],
        y=entries['entry_price'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'
    ))

    # Add exit markers
    exits = trade_history.dropna(subset=['exit_date'])
    fig.add_trace(go.Scatter(
        x=exits['exit_date'],
        y=exits['exit_price'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'
    ))

    # Add equity curve on secondary y-axis
    fig.add_trace(go.Scatter(
        x=equity_curve['date'],
        y=equity_curve['equity'],
        mode='lines',
        name='Equity Curve',
        line=dict(color='orange'),
        yaxis='y2'
    ))

    # Update layout for dual y-axes
    fig.update_layout(
        title='Asset Price and Equity Curve',
        xaxis_title='Date',
        yaxis=dict(
            title='Asset Price',
            side='left'
        ),
        yaxis2=dict(
            title='Equity',
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0, y=1.2)
    )

    fig.show()
