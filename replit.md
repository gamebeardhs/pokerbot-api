# Overview

A FastAPI-based poker advisory service that provides mathematically optimal Game Theory Optimal (GTO) decisions using OpenSpiel's Counterfactual Regret Minimization (CFR) algorithms. The service offers real-time poker decision recommendations through a RESTful API with WebSocket support for live table state streaming. It's designed to compute Nash equilibrium strategies for Texas Hold'em poker situations with fast response times under 1 second.

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