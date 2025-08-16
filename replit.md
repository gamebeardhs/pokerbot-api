# Overview

A comprehensive FastAPI-based poker advisory service that provides mathematically optimal Game Theory Optimal (GTO) decisions using advanced poker analysis. The system now implements a true GTO bot with complete table analysis including board texture evaluation, range vs range analysis, position-aware strategy, opponent modeling, and stack depth considerations. The service offers real-time poker decision recommendations through a RESTful API with WebSocket support for live table state streaming, computing optimal strategies for Texas Hold'em poker situations with comprehensive analysis under 1 second.

## Recent Major Enhancements (August 2025)

The system has been significantly enhanced to become a true GTO bot with comprehensive poker analysis:

### Enhanced Data Models
- **Comprehensive TableState**: Now captures board texture, player ranges, effective stacks, SPR, betting history, and positional information
- **Advanced Decision Models**: Enhanced GTODecision with confidence, frequency, reasoning, and alternative actions
- **Detailed Metrics**: EquityBreakdown with fold equity, realize equity, and range-based calculations
- **Opponent Modeling**: PlayerStats tracking VPIP, PFR, aggression factor, and positional tendencies

### Core Analysis Components
- **Board Texture Analyzer**: Evaluates board wetness, connectivity, draw potential, and strategic implications
- **Range Analyzer**: Estimates opponent ranges, calculates range vs range equity, and analyzes hand distributions
- **Position Strategy**: Implements position-aware decisions with proper ranges and betting frequencies
- **Opponent Modeling**: Tracks player tendencies and provides exploitative adjustments

### Enhanced Decision Engine
- **Multi-Component Analysis**: Integrates CFR, board analysis, range analysis, and opponent modeling
- **True GTO Calculations**: Proper stack-to-pot ratio considerations and effective stack analysis
- **Position-Aware Betting**: Dynamic bet sizing based on position, board texture, and opponent types
- **Exploitative Adjustments**: Adapts GTO baseline based on opponent weaknesses and table dynamics

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **FastAPI**: Chosen for high-performance async API with automatic OpenAPI documentation
- **Uvicorn**: ASGI server for production deployment
- **WebSocket Support**: Real-time streaming for live table updates
- **Bearer Token Authentication**: Secure API access for production use

## Core Decision Engine
- **OpenSpiel Integration**: Uses CFR (Counterfactual Regret Minimization) algorithms for true GTO computations
- **Table State Adapter**: Converts JSON input to OpenSpiel-compatible game format
- **Strategy Cache**: LRU cache with TTL for pre-computed solutions to common situations
- **Multiple Strategy Support**: Configurable strategies for different game types (cash games, tournaments)

## API Design
- **RESTful Endpoints**: Standard HTTP methods for decision requests and health checks
- **Pydantic Models**: Request/response validation and serialization
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **CORS Support**: Cross-origin resource sharing for web clients

## Data Models
- **TableState**: Complete poker table information including seats, cards, pot sizes, and betting rounds
- **GTOResponse**: Decision recommendations with equity calculations and strategy metrics
- **Seat Management**: Player position tracking and stack size monitoring
- **Card Representation**: String format conversion to OpenSpiel integer encoding

## Strategy System
- **JSON Configuration**: Strategy parameters stored in easily editable JSON files
- **Game Type Specific**: Separate strategies for cash games and tournaments
- **Preflop Ranges**: Position-based opening and 3-betting ranges
- **Postflop Logic**: Betting frequencies and sizing recommendations

## Performance Optimizations
- **Strategy Caching**: Avoid recomputing identical game situations
- **Async Processing**: Non-blocking decision computation
- **Fast CFR Solving**: Optimized iteration limits for sub-second responses
- **Memory Management**: LRU cache with configurable size limits

# External Dependencies

## Core Libraries
- **FastAPI**: Web framework for API development
- **Uvicorn**: ASGI server for running the application
- **Pydantic**: Data validation and serialization
- **OpenSpiel**: Game theory library for CFR algorithms (optional dependency)

## Python Standard Libraries
- **asyncio**: Asynchronous programming support
- **logging**: Application logging and monitoring
- **json**: Strategy configuration file parsing
- **collections**: OrderedDict for LRU cache implementation
- **datetime**: Timestamp handling for requests and caching

## Development and Testing
- **pytest**: Unit testing framework
- **pytest-asyncio**: Async test support

## Optional Dependencies
- **OpenSpiel**: Required for true GTO computations (graceful degradation if unavailable)
- **NumPy**: Mathematical computations for equity calculations
- **Pandas**: Data manipulation if needed for advanced analytics

## Configuration
- **Environment Variables**: LOG_LEVEL for runtime configuration
- **JSON Strategy Files**: External configuration for poker strategies
- **Bearer Token**: API authentication (configured via environment)