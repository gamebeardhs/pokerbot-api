"""
GTO Database System for Instant Poker Recommendations
Combines precomputed CFR solutions with fast similarity search using HNSW.
"""

import sqlite3
import numpy as np
import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading

from .poker_vectorizer import PokerVectorizer, PokerSituation

# Handle optional hnswlib import
try:
    import hnswlib
    HNSWLIB_AVAILABLE = True
except ImportError:
    HNSWLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

@dataclass
class GTOSolution:
    """Precomputed GTO solution for a poker situation."""
    situation_id: str
    vector: np.ndarray
    recommendation: str  # 'fold', 'call', 'raise'
    bet_size: Optional[float]
    equity: float
    reasoning: str
    cfr_confidence: float
    metadata: Dict[str, Any]

class GTODatabase:
    """High-performance GTO recommendation database with similarity search."""
    
    def __init__(self, db_path: str = "gto_database.db", index_path: str = "gto_index.bin"):
        self.db_path = Path(db_path)
        self.index_path = Path(index_path)
        self.vectorizer = PokerVectorizer()
        self.gto_service = None  # Will be lazy-loaded
        
        # HNSW Index for similarity search
        self.dimension = 32
        self.max_elements = 100000
        self.hnsw_index = None
        
        # Thread safety
        self.lock = threading.RLock()
        self.initialized = False
        
        # Performance tracking
        self.query_count = 0
        self.total_query_time = 0.0
        
    def initialize(self):
        """Initialize database and HNSW index."""
        with self.lock:
            if self.initialized:
                return
                
            logger.info("Initializing GTO database system...")
            
            # Create database tables
            self._create_database()
            
            # Initialize or load HNSW index
            self._initialize_hnsw_index()
            
            # Check if database needs population
            situation_count = self._get_situation_count()
            if situation_count == 0:
                logger.info("Empty database detected, starting population...")
                self._populate_database(initial_count=1000)
            else:
                logger.info(f"Database contains {situation_count} situations")
            
            self.initialized = True
            logger.info("GTO database system ready")
    
    def _create_database(self):
        """Create SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gto_situations (
                    id TEXT PRIMARY KEY,
                    vector BLOB NOT NULL,
                    hole_cards TEXT NOT NULL,
                    board_cards TEXT,
                    position INTEGER NOT NULL,
                    pot_size REAL NOT NULL,
                    bet_to_call REAL NOT NULL,
                    stack_size REAL NOT NULL,
                    betting_round INTEGER NOT NULL,
                    recommendation TEXT NOT NULL,
                    bet_size REAL,
                    equity REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    cfr_confidence REAL NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recommendation 
                ON gto_situations(recommendation)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_betting_round 
                ON gto_situations(betting_round)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_equity 
                ON gto_situations(equity)
            """)
    
    def _initialize_hnsw_index(self):
        """Initialize HNSW index for fast similarity search."""
        if not HNSWLIB_AVAILABLE:
            logger.warning("HNSW not available, using fallback search")
            self.hnsw_index = None
            return
            
        self.hnsw_index = hnswlib.Index(space='cosine', dim=self.dimension)
        
        if self.index_path.exists():
            logger.info("Loading existing HNSW index...")
            try:
                self.hnsw_index.load_index(str(self.index_path))
                logger.info(f"HNSW index loaded: {self.hnsw_index.get_current_count()} elements")
                return
            except Exception as e:
                logger.warning(f"Failed to load index: {e}, creating new one")
        
        # Initialize new index
        self.hnsw_index.init_index(
            max_elements=self.max_elements,
            ef_construction=200,
            M=16
        )
        self.hnsw_index.set_ef(50)  # Query time parameter
    
    def _get_situation_count(self) -> int:
        """Get total number of situations in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM gto_situations")
            return cursor.fetchone()[0]
    
    def get_instant_recommendation(self, situation: PokerSituation, 
                                 top_k: int = 5) -> Optional[Dict[str, Any]]:
        """Get instant GTO recommendation using similarity search."""
        if not self.initialized:
            self.initialize()
            
        start_time = time.time()
        
        try:
            with self.lock:
                # Vectorize the situation
                query_vector = self.vectorizer.vectorize_situation(situation)
                
                # Find similar situations using HNSW or fallback
                if self.hnsw_index is None:
                    # Fallback: simple vector similarity search
                    return self._fallback_similarity_search(query_vector, top_k)
                
                if self.hnsw_index.get_current_count() == 0:
                    logger.warning("No situations in database for similarity search")
                    return None
                
                labels, distances = self.hnsw_index.knn_query(query_vector, k=top_k)
                
                # Get the most similar situation from database
                best_match = self._get_situation_by_id(labels[0])
                if best_match is None:
                    return None
                
                # Track performance
                query_time = time.time() - start_time
                self.query_count += 1
                self.total_query_time += query_time
                
                logger.info(f"Instant recommendation found in {query_time*1000:.1f}ms "
                          f"(similarity: {1-distances[0]:.3f})")
                
                # Return formatted response - using dictionary format for now
                return {
                    'decision': best_match['recommendation'],
                    'bet_size': best_match.get('bet_size', 0),
                    'reasoning': f"Similar situation analysis: {best_match['reasoning']}",
                    'equity': best_match['equity'],
                    'confidence': best_match['cfr_confidence'] * (1 - distances[0]),  # Adjust for similarity
                    'strategy': 'database_lookup',
                    'metrics': {
                        'source': 'database_lookup',
                        'similarity_score': 1 - distances[0],
                        'query_time_ms': query_time * 1000,
                        'similar_situations': len(labels)
                    }
                }
                
        except Exception as e:
            logger.error(f"Database lookup failed: {e}")
            return None
    
    def _get_situation_by_id(self, situation_id: int) -> Optional[Dict[str, Any]]:
        """Get situation details by HNSW index ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM gto_situations 
                WHERE rowid = ? + 1
            """, (situation_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def add_solution(self, situation: PokerSituation, solution: Dict[str, Any]) -> bool:
        """Add new GTO solution to database and index."""
        if not self.initialized:
            self.initialize()
            
        try:
            with self.lock:
                # Generate unique ID
                situation_id = self._generate_situation_id(situation)
                
                # Vectorize situation
                vector = self.vectorizer.vectorize_situation(situation)
                vector_blob = vector.tobytes()
                
                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO gto_situations 
                        (id, vector, hole_cards, board_cards, position, pot_size, 
                         bet_to_call, stack_size, betting_round, recommendation, 
                         bet_size, equity, reasoning, cfr_confidence, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        situation_id,
                        vector_blob,
                        json.dumps(situation.hole_cards),
                        json.dumps(situation.board_cards),
                        situation.position.value,
                        situation.pot_size,
                        situation.bet_to_call,
                        situation.stack_size,
                        situation.betting_round.value,
                        solution['decision'],
                        solution.get('bet_size', 0),
                        solution.get('equity', 0.0),
                        solution.get('reasoning', ''),
                        solution.get('confidence', 0.0),
                        json.dumps(solution.get('metadata', {}))
                    ))
                
                # Add to HNSW index
                current_count = 0
                if self.hnsw_index is not None:
                    current_count = self.hnsw_index.get_current_count()
                    self.hnsw_index.add_items(vector, current_count)
                
                logger.debug(f"Added situation {situation_id} to database (total: {current_count + 1})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add solution: {e}")
            return False
    
    def _populate_database(self, initial_count: int = 1000):
        """Populate database with initial GTO solutions using simplified approach."""
        logger.info(f"Generating {initial_count} initial GTO solutions...")
        
        # Generate test situations using vectorizer
        situations = self.vectorizer.create_test_situations(initial_count)
        
        processed = 0
        
        # Use simplified rule-based GTO for initial population
        for situation, vector in situations:
            try:
                # Generate simplified GTO decision based on situation
                gto_response = self._generate_simple_gto_solution(situation)
                if gto_response:
                    self.add_solution(situation, gto_response)
                    processed += 1
                    
                    if processed % 50 == 0:
                        logger.info(f"Generated {processed}/{initial_count} solutions...")
                        
            except Exception as e:
                logger.warning(f"Failed to generate solution for situation: {e}")
                continue
        
        # Save HNSW index
        if self.hnsw_index and self.hnsw_index.get_current_count() > 0:
            self.hnsw_index.save_index(str(self.index_path))
            logger.info(f"Database populated with {processed} solutions, index saved")
    
    def _generate_cfr_solution(self, situation: PokerSituation) -> Optional[Dict[str, Any]]:
        """Generate authentic CFR solution for a situation."""
        try:
            # Lazy-load GTO service
            if self.gto_service is None:
                from ..advisor.enhanced_gto_service import EnhancedGTODecisionService
                self.gto_service = EnhancedGTODecisionService()
            
            # Convert to table state format expected by GTO service
            table_state = {
                "hero_cards": situation.hole_cards,
                "board": situation.board_cards,
                "pot_size": situation.pot_size,
                "bet_to_call": situation.bet_to_call,
                "stack_size": situation.stack_size,
                "position": situation.position.name.lower(),
                "num_players": situation.num_players,
                "betting_round": situation.betting_round.name.lower()
            }
            
            # Get GTO recommendation with timeout 
            from ..api.models import TableState, Seat, Stakes
            
            # Create proper TableState object
            table_state_obj = TableState(
                table_id="db_gen",
                hand_id="db_gen",
                room="database",
                variant="nlhe",
                max_seats=9,
                hero_seat=1,
                stakes=Stakes(sb=0.5, bb=1.0),
                street=situation.betting_round.name.lower(),
                board=situation.board_cards,
                pot=situation.pot_size,
                seats=[
                    Seat(
                        seat=1,
                        name="Hero",
                        stack=situation.stack_size,
                        in_hand=True,
                        is_hero=True,
                        position=situation.position.name,
                        hole_cards=situation.hole_cards
                    )
                ]
            )
            
            import asyncio
            response = asyncio.run(self.gto_service.compute_gto_decision(table_state_obj))
            
            # Convert GTOResponse to our format
            if response and hasattr(response, 'decision'):
                return {
                    'decision': response.decision.action if hasattr(response.decision, 'action') else 'fold',
                    'bet_size': response.decision.bet_size if hasattr(response.decision, 'bet_size') else 0,
                    'equity': response.metrics.equity.total if hasattr(response, 'metrics') and hasattr(response.metrics, 'equity') else 0.0,
                    'reasoning': response.reasoning or 'GTO analysis',
                    'confidence': response.metrics.confidence if hasattr(response, 'metrics') else 0.8,
                    'metadata': {'source': 'cfr_computation'}
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"CFR generation failed: {e}")
            return None
    
    def _generate_simple_gto_solution(self, situation: PokerSituation) -> Optional[Dict[str, Any]]:
        """Generate simplified GTO solution using rule-based approach."""
        try:
            # Calculate basic hand strength
            hand_strength = self._calculate_hand_strength(situation.hole_cards, situation.board_cards)
            
            # Calculate pot odds
            pot_odds = situation.bet_to_call / (situation.pot_size + situation.bet_to_call) if (situation.pot_size + situation.bet_to_call) > 0 else 0
            
            # Basic GTO decision tree
            decision = "fold"
            bet_size = 0
            equity = hand_strength
            confidence = 0.75
            
            # Simple decision logic
            if situation.bet_to_call == 0:  # No bet to call
                if hand_strength > 0.6:
                    decision = "raise" if situation.position.value >= 6 else "call"
                    bet_size = situation.pot_size * 0.75
                elif hand_strength > 0.4:
                    decision = "call"
                else:
                    decision = "check"
            else:  # Facing a bet
                if hand_strength > pot_odds + 0.1:  # Good odds with margin
                    if hand_strength > 0.7:
                        decision = "raise"
                        bet_size = situation.pot_size * 0.8
                    else:
                        decision = "call"
                elif hand_strength > pot_odds - 0.05:  # Marginal
                    decision = "call" if situation.position.value >= 5 else "fold"
                else:
                    decision = "fold"
            
            # Adjust for position
            if situation.position.value >= 7:  # Button/SB - more aggressive
                confidence += 0.1
                if decision == "call" and hand_strength > 0.5:
                    decision = "raise"
                    bet_size = situation.pot_size * 0.6
            
            # Adjust for stack depth
            spr = situation.stack_size / max(situation.pot_size, 1)
            if spr < 3 and hand_strength > 0.6:  # Short stack, more aggressive
                if decision == "call":
                    decision = "raise"
                    bet_size = min(situation.stack_size, situation.pot_size)
            
            reasoning = f"Hand strength: {hand_strength:.2f}, Pot odds: {pot_odds:.2f}, Position: {situation.position.name}, SPR: {spr:.1f}"
            
            return {
                'decision': decision,
                'bet_size': bet_size,
                'equity': equity,
                'reasoning': reasoning,
                'confidence': min(confidence, 1.0),
                'metadata': {'source': 'rule_based_gto', 'hand_strength': hand_strength}
            }
            
        except Exception as e:
            logger.warning(f"Simple GTO generation failed: {e}")
            return None
    
    def _calculate_hand_strength(self, hole_cards: List[str], board_cards: List[str]) -> float:
        """Calculate normalized hand strength (0-1)."""
        try:
            if len(hole_cards) != 2:
                return 0.3
                
            # Parse cards
            card1, card2 = hole_cards[0], hole_cards[1]
            rank1 = self._card_rank_value(card1[0])
            rank2 = self._card_rank_value(card2[0])
            suited = card1[1] == card2[1]
            
            # Basic preflop strength
            pair_bonus = 0.3 if rank1 == rank2 else 0
            high_card_bonus = max(rank1, rank2) / 14.0 * 0.4
            suited_bonus = 0.1 if suited else 0
            connector_bonus = 0.05 if abs(rank1 - rank2) <= 2 else 0
            
            preflop_strength = min(pair_bonus + high_card_bonus + suited_bonus + connector_bonus, 0.9)
            
            # If no board, return preflop strength
            if not board_cards:
                return preflop_strength
            
            # Simple postflop evaluation
            board_ranks = [self._card_rank_value(card[0]) for card in board_cards if len(card) >= 2]
            hole_ranks = [rank1, rank2]
            
            # Check for pairs
            all_ranks = hole_ranks + board_ranks
            rank_counts = {}
            for rank in all_ranks:
                rank_counts[rank] = rank_counts.get(rank, 0) + 1
            
            # Strength modifiers
            pair_strength = 0
            for rank, count in rank_counts.items():
                if count >= 2 and rank in hole_ranks:
                    pair_strength = 0.6 + (count - 2) * 0.2  # Pair/trips/quads
                    break
            
            # High card strength
            high_card_strength = max(hole_ranks) / 14.0 * 0.3
            
            return min(max(preflop_strength, pair_strength) + high_card_strength, 1.0)
            
        except Exception:
            return 0.4  # Default moderate strength
    
    def _card_rank_value(self, rank: str) -> int:
        """Convert card rank to numerical value."""
        rank_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        return rank_map.get(rank, int(rank) if rank.isdigit() else 7)
    
    def _generate_situation_id(self, situation: PokerSituation) -> str:
        """Generate unique ID for situation."""
        import hashlib
        
        situation_str = f"{situation.hole_cards}_{situation.board_cards}_{situation.position.value}_{situation.pot_size}_{situation.bet_to_call}_{situation.betting_round.value}"
        return hashlib.md5(situation_str.encode()).hexdigest()[:12]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        with self.lock:
            avg_query_time = (self.total_query_time / self.query_count * 1000 
                            if self.query_count > 0 else 0)
            
            return {
                'total_situations': self._get_situation_count(),
                'hnsw_index_size': self.hnsw_index.get_current_count() if self.hnsw_index else 0,
                'total_queries': self.query_count,
                'average_query_time_ms': avg_query_time,
                'database_size_mb': self.db_path.stat().st_size / 1024 / 1024 if self.db_path.exists() else 0
            }
    
    def rebuild_index(self):
        """Rebuild HNSW index from database."""
        logger.info("Rebuilding HNSW index from database...")
        
        with self.lock:
            # Initialize new index
            self._initialize_hnsw_index()
            
            # Load all vectors from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT vector FROM gto_situations ORDER BY rowid")
                vectors = []
                for row in cursor:
                    vector = np.frombuffer(row[0], dtype=np.float32)
                    vectors.append(vector)
                
                if vectors and self.hnsw_index:
                    # Add all vectors to index
                    vectors_array = np.array(vectors)
                    ids = np.arange(len(vectors))
                    self.hnsw_index.add_items(vectors_array, ids)
                    
                    # Save index
                    self.hnsw_index.save_index(str(self.index_path))
                    logger.info(f"Index rebuilt with {len(vectors)} vectors")

    def _fallback_similarity_search(self, query_vector: np.ndarray, top_k: int = 5) -> Optional[Dict[str, Any]]:
        """Fallback similarity search using database queries when HNSW unavailable."""
        try:
            # Get all vectors from database for comparison
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT rowid, vector, recommendation, bet_size, equity, reasoning, cfr_confidence FROM gto_situations LIMIT 1000")
                
                best_similarity = -1
                best_match = None
                
                for row in cursor:
                    db_vector = np.frombuffer(row[1], dtype=np.float32)
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_vector, db_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(db_vector)
                    )
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = {
                            'recommendation': row[2],
                            'bet_size': row[3],
                            'equity': row[4], 
                            'reasoning': row[5],
                            'cfr_confidence': row[6]
                        }
                
                if best_match and best_similarity > 0.7:  # Minimum similarity threshold
                    return {
                        'decision': best_match['recommendation'],
                        'bet_size': best_match.get('bet_size', 0),
                        'reasoning': f"Fallback similarity analysis: {best_match['reasoning']}",
                        'equity': best_match['equity'],
                        'confidence': best_match['cfr_confidence'] * best_similarity,
                        'strategy': 'fallback_similarity',
                        'metrics': {
                            'source': 'fallback_similarity',
                            'similarity_score': best_similarity,
                            'method': 'cosine_similarity'
                        }
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Fallback similarity search failed: {e}")
            return None

# Global database instance
gto_db = GTODatabase()