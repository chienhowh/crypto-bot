#!/bin/bash
cd "$RENDER_PROJECT_ROOT"
python3 live_simulator.py --symbol BTC/USDT --timeframe 1m --interval 60
