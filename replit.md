# Overview

This project provides a comprehensive FastAPI-based poker advisory service, delivering mathematically optimal Game Theory Optimal (GTO) decisions. It functions as a professional-grade poker bot, designed for maximum stealth and accuracy. The system incorporates a 6-phase decision-making process, circuit breaker protection, advanced stealth detection, GPU acceleration, enhanced GTO analysis, turn detection, and anti-detection measures. The business vision is to offer a highly accurate and undetectable poker advisory tool for professional use, outperforming standard analysis tools through advanced computer vision and authentic GTO algorithms. The system features a unified interface with transparent mathematical reasoning, providing detailed CFR-based analysis for every recommendation. It is optimized for Windows desktop, with specialized setup scripts and one-click startup.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **FastAPI**: Used for high-performance async APIs with automatic OpenAPI documentation.
- **Uvicorn**: Serves as the ASGI server.
- **WebSocket Support**: Enables real-time streaming for live table updates.
- **Bearer Token Authentication**: Provides secure API access.

## Core Decision Engine
- **OpenSpiel Integration**: Utilizes CFR algorithms for true GTO computations.
- **Table State Adapter**: Converts JSON input into an OpenSpiel-compatible game format.
- **Strategy Cache**: An LRU cache with TTL for pre-computed solutions.
- **Multiple Strategy Support**: Configurable strategies for different game types.

## API Design
- **RESTful Endpoints**: Standard HTTP methods for decision requests and health checks.
- **Pydantic Models**: For request/response validation and serialization.
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes.
- **CORS Support**: Cross-origin resource sharing enabled for web clients.

## Data Models
- **TableState**: Captures complete poker table information (seats, cards, pot sizes, betting rounds).
- **GTOResponse**: Provides decision recommendations with equity calculations and strategy metrics.
- **Seat Management**: Tracks player positions and stack sizes.
- **Card Representation**: Handles string format conversion to OpenSpiel integer encoding.

## Strategy System
- **JSON Configuration**: Strategy parameters stored in editable JSON files.
- **Game Type Specific**: Separate strategies for cash games and tournaments.
- **Preflop Ranges**: Position-based opening and 3-betting ranges.
- **Postflop Logic**: Includes betting frequencies and sizing recommendations.

## Performance Optimizations
- **Strategy Caching**: Prevents recomputing identical game situations.
- **Async Processing**: Enables non-blocking decision computation.
- **Fast CFR Solving**: Optimized iteration limits for sub-second responses.
- **Memory Management**: LRU cache with configurable size limits.

## Computer Vision & Anti-Detection
- **Dual Recognition Approach**: Combines template matching with neural network fallback for card recognition.
- **Template-Based Training**: Automatic dataset generation with data augmentation for robust recognition.
- **Color Normalization**: Advanced color standardization for consistent card recognition.
- **Human Behavior Simulation**: Incorporates realistic timing variations and multiple behavior profiles for anti-detection.
- **Intelligent Auto-Calibration**: Automatically detects and calibrates ACR tables using multi-layer recognition (template matching, OCR, pixel analysis).
- **GPU Acceleration**: Utilizes CUDA for accelerated computer vision, with automatic CPU fallback.
- **Dynamic Window Detection**: Uses relative positioning instead of fixed pixel coordinates, adapting to ACR window position or size.
- **Windows Optimization**: Includes MSS window capture, field-specific OCR, robust turn detection, state stabilization, FPS anti-detection (random timing jitter), percentage-based regions, and DPI awareness (per-monitor v2 support).

# External Dependencies

## Core Libraries
- **FastAPI**: Web framework for API development.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and serialization.
- **OpenSpiel**: Game theory library for CFR algorithms.

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
- **EasyOCR**: For enhanced OCR accuracy.
- **Tesseract**: OCR engine used in conjunction with EasyOCR for multi-engine consensus.
- **PyAutoGUI**: Fallback for Windows screen capture.
```