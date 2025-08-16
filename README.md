# Poker GTO Advisory Service

A FastAPI-based poker advisory service providing mathematically optimal GTO decisions using OpenSpiel's Counterfactual Regret Minimization (CFR) algorithms.

## Overview

This service provides real-time Game Theory Optimal (GTO) poker decision recommendations through a RESTful API. It uses OpenSpiel's CFR solver to compute Nash equilibrium strategies for Texas Hold'em poker scenarios.

### Key Features

- **True GTO Analysis**: Uses OpenSpiel CFR algorithms for mathematically optimal decisions
- **Fast Response Times**: Optimized for <1 second decision computation
- **Real-time Updates**: WebSocket support for live table state streaming  
- **Strategy Caching**: Pre-computed solutions for common poker situations
- **Bearer Token Security**: API authentication for production use
- **Comprehensive Metrics**: Equity, EV, and exploitability measurements

## Architecture

