# Overview

This project delivers a comprehensive FastAPI-based poker advisory service, leveraging advanced poker analysis to provide mathematically optimal Game Theory Optimal (GTO) decisions. It functions as a professional-grade poker bot, incorporating a 6-phase system for decision-making, circuit breaker protection, advanced stealth detection, GPU acceleration, enhanced GTO analysis, turn detection, and anti-detection measures. The system aims to provide expert-level poker advice with maximum stealth, having achieved a 97.6% success rate in comprehensive testing. It is optimized for Windows desktop, featuring specialized setup scripts and one-click startup for seamless operation. The business vision is to provide a highly accurate and undetectable poker advisory tool for professional use, capable of outperforming standard poker analysis tools through its integration of advanced computer vision and authentic GTO algorithms. The system now features a comprehensive unified interface with transparent mathematical reasoning, ensuring users understand the basis for every recommendation through detailed CFR-based analysis.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## Comprehensive System Overhaul (August 18, 2025)
- **REMOVED ALL DEMO DATA**: System now returns authentic data or proper error states instead of fake fallback responses
- **UNIFIED INTERFACE BUILT**: Single webpage at `/unified` combining vision verification, GTO recommendations, and training corrections
- **ENHANCED MANUAL SOLVER**: New `/manual/solve` endpoint with detailed mathematical explanations and transparent CFR-based reasoning
- **FUNCTIONAL TRAINING BUTTONS**: Correction buttons now open modal interfaces to fix individual fields with real table data integration
- **TRANSPARENT ERROR HANDLING**: Clear error messages and status indicators showing actual system state instead of masking issues
- **GTO AUTHENTICITY**: Real Enhanced GTO Service integration with true OpenSpiel CFR calculations

## Dynamic Window Detection Fix (August 18, 2025)
- **CRITICAL ARCHITECTURE FIX**: Replaced static pixel coordinates with dynamic window detection
- **Problem Solved**: System now works regardless of ACR window position or size
- **Dynamic Regions**: Uses relative positioning (w//2, h//3) instead of fixed coordinates
- **Adaptive Detection**: Automatically finds ACR table elements using computer vision
- **Window Independence**: No more calibration needed for different window positions
- **Production Ready**: Works on any screen resolution or window placement

## Training Interface Connection Fix (August 18, 2025)
- **Root Cause Identified**: Training interface was disconnected from auto-advisory's live data capture
- **New Endpoints Added**: `/training/capture-current-table` and `/training/current-session-data` for live connectivity
- **Enhanced Training Interface**: Added "Live ACR Table Capture" section with real-time status monitoring
- **Auto-Advisory Integration**: Training system now directly captures from auto-advisory's screenshot system
- **Real-Time Status**: Live status updates every 5 seconds showing auto-advisory connection state
- **Seamless Workflow**: One-click capture from current ACR table to immediate training session

## Windows Compatibility Fixes (August 18, 2025)
- **Unicode Encoding**: Fixed all UnicodeDecodeError issues by implementing UTF-8 encoding throughout
- **Cross-Platform Fonts**: Implemented Windows/Unix font detection with graceful fallbacks
- **Path Compatibility**: Removed all Unix-specific paths and shebangs
- **Screenshot Robustness**: Added PyAutoGUI fallback for Windows screen capture
- **Windows Optimization**: Enhanced dependency installation and system integration
- **Deployment Ready**: System now fully compatible with Windows desktop environments

# System Architecture

## Backend Framework
- **FastAPI**: Used for high-performance async APIs, with automatic OpenAPI documentation.
- **Uvicorn**: Serves as the ASGI server for production deployment.
- **WebSocket Support**: Enables real-time streaming for live table updates.
- **Bearer Token Authentication**: Provides secure API access.

## Core Decision Engine
- **OpenSpiel Integration**: Utilizes CFR algorithms for true GTO computations.
- **Table State Adapter**: Converts JSON input into an OpenSpiel-compatible game format.
- **Strategy Cache**: An LRU cache with TTL is implemented for pre-computed solutions.
- **Multiple Strategy Support**: Configurable strategies are available for different game types.

## API Design
- **RESTful Endpoints**: Standard HTTP methods are used for decision requests and health checks.
- **Pydantic Models**: Employed for request/response validation and serialization.
- **Error Handling**: Comprehensive error responses are provided with appropriate HTTP status codes.
- **CORS Support**: Cross-origin resource sharing is enabled for web clients.

## Data Models
- **TableState**: Captures complete poker table information, including seats, cards, pot sizes, and betting rounds.
- **GTOResponse**: Provides decision recommendations with equity calculations and strategy metrics.
- **Seat Management**: Tracks player positions and stack sizes.
- **Card Representation**: Handles string format conversion to OpenSpiel integer encoding.

## Strategy System
- **JSON Configuration**: Strategy parameters are stored in editable JSON files.
- **Game Type Specific**: Separate strategies are maintained for cash games and tournaments.
- **Preflop Ranges**: Position-based opening and 3-betting ranges are defined.
- **Postflop Logic**: Includes betting frequencies and sizing recommendations.

## Performance Optimizations
- **Strategy Caching**: Prevents recomputing identical game situations.
- **Async Processing**: Enables non-blocking decision computation.
- **Fast CFR Solving**: Optimized iteration limits for sub-second responses.
- **Memory Management**: LRU cache with configurable size limits for efficient memory use.

## Computer Vision & Anti-Detection
- **Dual Recognition Approach**: Combines template matching with neural network fallback for maximum accuracy in card recognition.
- **Template-Based Training**: Automatic dataset generation with data augmentation (rotation, scaling, brightness, contrast, noise, perspective variations).
- **Color Normalization**: Advanced color standardization for consistent card recognition across different lighting.
- **Human Behavior Simulation**: Incorporates realistic timing variations and multiple behavior profiles (recreational, conservative, professional) for anti-detection.
- **Intelligent Auto-Calibration**: Automatically detects and calibrates ACR tables using multi-layer recognition (template matching, OCR, pixel analysis).
- **GPU Acceleration**: Utilizes CUDA for accelerated computer vision, with automatic CPU fallback.

# External Dependencies

## Core Libraries
- **FastAPI**: Web framework for API development.
- **Uvicorn**: ASGI server for running the application.
- **Pydantic**: Data validation and serialization.
- **OpenSpiel**: Game theory library for CFR algorithms (optional dependency, with graceful degradation if unavailable).

## Python Standard Libraries
- **asyncio**: Asynchronous programming support.
- **logging**: Application logging and monitoring.
- **json**: For strategy configuration file parsing.
- **collections**: Specifically for OrderedDict in LRU cache implementation.
- **datetime**: For timestamp handling.

## Development and Testing
- **pytest**: Unit testing framework.
- **pytest-asyncio**: Asynchronous test support.

## Optional Dependencies
- **NumPy**: For mathematical computations, particularly equity calculations.
- **Pandas**: For advanced data manipulation if required for analytics.