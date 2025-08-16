"""Test runner for validating scraper functionality."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.scraper.acr_scraper import ACRScraper
from app.scraper.clubwpt_scraper import ClubWPTGoldScraper
from app.api.models import TableState, Stakes, Seat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperValidator:
    """Validates that scrapers extract complete and valid data."""
    
    def __init__(self):
        self.required_fields = {
            'basic': ['table_id', 'street', 'pot', 'stakes', 'seats', 'max_seats'],
            'enhanced': [
                'hero_seat', 'button_seat', 'effective_stacks', 'spr',
                'current_action_type', 'num_raises_this_street'
            ],
            'seat_fields': ['seat', 'name', 'stack', 'in_hand', 'position']
        }
    
    def validate_table_data(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scraped table data completeness and format."""
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'valid': True,
            'errors': [],
            'warnings': [],
            'completeness': {},
            'data_sample': {}
        }
        
        # Check basic required fields
        basic_complete = 0
        for field in self.required_fields['basic']:
            if field in table_data and table_data[field] is not None:
                basic_complete += 1
            else:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        validation_result['completeness']['basic'] = f"{basic_complete}/{len(self.required_fields['basic'])}"
        
        # Check enhanced fields
        enhanced_complete = 0
        for field in self.required_fields['enhanced']:
            if field in table_data and table_data[field] is not None:
                enhanced_complete += 1
            else:
                validation_result['warnings'].append(f"Missing enhanced field: {field}")
        
        validation_result['completeness']['enhanced'] = f"{enhanced_complete}/{len(self.required_fields['enhanced'])}"
        
        # Validate stakes data
        if 'stakes' in table_data:
            stakes = table_data['stakes']
            if not isinstance(stakes, dict) or 'sb' not in stakes or 'bb' not in stakes:
                validation_result['errors'].append("Invalid stakes format")
                validation_result['valid'] = False
            else:
                validation_result['data_sample']['stakes'] = f"${stakes.get('sb', 0)}/{stakes.get('bb', 0)}"
        
        # Validate seats data
        if 'seats' in table_data and table_data['seats']:
            seats = table_data['seats']
            seat_validation = self._validate_seats(seats)
            validation_result['completeness']['seats'] = seat_validation['completeness']
            validation_result['errors'].extend(seat_validation['errors'])
            validation_result['warnings'].extend(seat_validation['warnings'])
            validation_result['data_sample']['players'] = len(seats)
            
            # Check if hero is identified
            hero_found = any(seat.get('is_hero') for seat in seats)
            if not hero_found:
                validation_result['warnings'].append("Hero seat not identified")
        
        # Validate cards data
        card_validation = self._validate_cards(table_data)
        validation_result['data_sample'].update(card_validation)
        
        # Check position assignments
        if 'seats' in table_data:
            positioned_players = sum(1 for seat in table_data['seats'] if seat.get('position'))
            validation_result['data_sample']['positioned_players'] = positioned_players
            
            if positioned_players == 0:
                validation_result['warnings'].append("No player positions assigned")
        
        return validation_result
    
    def _validate_seats(self, seats: list) -> Dict[str, Any]:
        """Validate seat data structure."""
        result = {'errors': [], 'warnings': [], 'completeness': '0/0'}
        
        if not seats:
            result['errors'].append("No seat data found")
            return result
        
        complete_seats = 0
        for i, seat in enumerate(seats):
            seat_complete = 0
            for field in self.required_fields['seat_fields']:
                if field in seat and seat[field] is not None:
                    seat_complete += 1
                elif field in ['name', 'stack']:  # Critical fields
                    result['warnings'].append(f"Seat {i+1} missing {field}")
            
            if seat_complete >= 3:  # At least seat, stack, in_hand
                complete_seats += 1
        
        result['completeness'] = f"{complete_seats}/{len(seats)}"
        return result
    
    def _validate_cards(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate card data format."""
        card_info = {}
        
        # Hero cards
        hero_cards = table_data.get('hero_hole', [])
        if hero_cards:
            card_info['hero_cards'] = len(hero_cards)
            if len(hero_cards) != 2:
                card_info['hero_cards_warning'] = f"Expected 2 cards, got {len(hero_cards)}"
        else:
            card_info['hero_cards'] = 0
        
        # Board cards
        board_cards = table_data.get('board', [])
        card_info['board_cards'] = len(board_cards)
        
        # Validate card format
        all_cards = hero_cards + board_cards
        invalid_cards = [card for card in all_cards if not self._is_valid_card_format(card)]
        if invalid_cards:
            card_info['invalid_cards'] = invalid_cards
        
        return card_info
    
    def _is_valid_card_format(self, card: str) -> bool:
        """Check if card is in valid format (e.g., 'ah', 'ks')."""
        if not isinstance(card, str) or len(card) != 2:
            return False
        
        rank = card[0].lower()
        suit = card[1].lower()
        
        valid_ranks = '23456789tjqka'
        valid_suits = 'hdcs'
        
        return rank in valid_ranks and suit in valid_suits
    
    def print_validation_report(self, validation: Dict[str, Any], scraper_name: str):
        """Print a formatted validation report."""
        print(f"\n{'='*50}")
        print(f"VALIDATION REPORT: {scraper_name}")
        print(f"{'='*50}")
        print(f"Timestamp: {validation['timestamp']}")
        print(f"Overall Valid: {'✅ YES' if validation['valid'] else '❌ NO'}")
        
        print(f"\nCOMPLETENESS:")
        for category, score in validation['completeness'].items():
            print(f"  {category.title()}: {score}")
        
        if validation['data_sample']:
            print(f"\nDATA SAMPLE:")
            for key, value in validation['data_sample'].items():
                print(f"  {key}: {value}")
        
        if validation['errors']:
            print(f"\n❌ ERRORS ({len(validation['errors'])}):")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print(f"\n⚠️  WARNINGS ({len(validation['warnings'])}):")
            for warning in validation['warnings'][:5]:  # Show first 5
                print(f"  - {warning}")
            if len(validation['warnings']) > 5:
                print(f"  ... and {len(validation['warnings']) - 5} more")


async def test_acr_scraper():
    """Test ACR scraper functionality."""
    print("Testing ACR Scraper...")
    
    scraper = ACRScraper()
    validator = ScraperValidator()
    
    # Check if scraper can be set up
    setup_success = scraper.setup()
    print(f"ACR Setup: {'✅ Success' if setup_success else '❌ Failed'}")
    
    if not setup_success:
        print("Cannot test ACR scraper - setup failed")
        return
    
    # Check if table is detected
    table_active = scraper.is_table_active()
    print(f"Table Detection: {'✅ Active' if table_active else '❌ No table detected'}")
    
    if not table_active:
        print("No ACR table detected. Please:")
        print("1. Open ACR poker client")
        print("2. Join a poker table")
        print("3. Run this test again")
        return
    
    # Test data extraction
    try:
        table_data = await scraper.scrape_table_state()
        
        if table_data:
            print("✅ Data extraction successful")
            
            # Validate the data
            validation = validator.validate_table_data(table_data)
            validator.print_validation_report(validation, "ACR Scraper")
            
            # Save sample data for inspection
            with open('acr_test_data.json', 'w') as f:
                json.dump(table_data, f, indent=2, default=str)
            print(f"\nSample data saved: acr_test_data.json")
            
        else:
            print("❌ Data extraction failed - no data returned")
            
    except Exception as e:
        print(f"❌ Data extraction error: {e}")
    
    finally:
        scraper.cleanup()


async def test_clubwpt_scraper():
    """Test ClubWPT scraper functionality."""
    print("Testing ClubWPT Scraper...")
    
    scraper = ClubWPTGoldScraper()
    validator = ScraperValidator()
    
    # Setup browser
    try:
        setup_success = await scraper.setup()
        print(f"ClubWPT Setup: {'✅ Success' if setup_success else '❌ Failed'}")
        
        if not setup_success:
            print("Cannot test ClubWPT scraper - setup failed")
            return
        
        # Manual navigation required
        print("Please manually:")
        print("1. Log in to ClubWPT Gold")
        print("2. Join a poker table")
        print("3. Press Enter when ready...")
        input()
        
        # Check table detection
        table_active = scraper.is_table_active()
        print(f"Table Detection: {'✅ Active' if table_active else '❌ No table detected'}")
        
        if not table_active:
            print("No ClubWPT table detected. Please join a table and try again.")
            return
        
        # Test data extraction
        table_data = await scraper.scrape_table_state()
        
        if table_data:
            print("✅ Data extraction successful")
            
            # Validate the data
            validation = validator.validate_table_data(table_data)
            validator.print_validation_report(validation, "ClubWPT Scraper")
            
            # Save sample data for inspection
            with open('clubwpt_test_data.json', 'w') as f:
                json.dump(table_data, f, indent=2, default=str)
            print(f"\nSample data saved: clubwpt_test_data.json")
            
        else:
            print("❌ Data extraction failed - no data returned")
            
    except Exception as e:
        print(f"❌ Scraper test error: {e}")
    
    finally:
        await scraper.cleanup()


async def test_data_conversion():
    """Test conversion of scraped data to TableState model."""
    print("\nTesting data conversion to TableState model...")
    
    test_files = ['acr_test_data.json', 'clubwpt_test_data.json']
    
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                table_data = json.load(f)
            
            print(f"\nTesting {test_file}...")
            
            # Convert to TableState model (same logic as scraper_manager)
            from app.api.models import TableState, Stakes, Seat
            
            # Convert seats
            seats = []
            for seat_data in table_data.get('seats', []):
                seat = Seat(**seat_data)
                seats.append(seat)
            
            # Convert stakes
            stakes_data = table_data.get('stakes', {})
            stakes = Stakes(**stakes_data)
            
            # Create TableState
            state = TableState(
                table_id=table_data.get('table_id', 'test'),
                street=table_data.get('street', 'PREFLOP'),
                board=table_data.get('board', []),
                hero_hole=table_data.get('hero_hole', []),
                pot=table_data.get('pot', 0),
                to_call=table_data.get('to_call', 0),
                bet_min=table_data.get('bet_min'),
                stakes=stakes,
                hero_seat=table_data.get('hero_seat'),
                max_seats=table_data.get('max_seats', 6),
                seats=seats
            )
            
            print(f"✅ {test_file} converts to TableState successfully")
            print(f"  Players: {len(state.seats)}")
            print(f"  Hero seat: {state.hero_seat}")
            print(f"  Stakes: ${state.stakes.sb}/${state.stakes.bb}")
            print(f"  Pot: ${state.pot}")
            
        except FileNotFoundError:
            print(f"⚠️  {test_file} not found - run scraper tests first")
        except Exception as e:
            print(f"❌ {test_file} conversion failed: {e}")


async def main():
    """Main test interface."""
    print("Poker Scraper Test Suite")
    print("=" * 40)
    print("1. Test ACR scraper")
    print("2. Test ClubWPT scraper")
    print("3. Test both scrapers")
    print("4. Test data conversion only")
    
    choice = input("Choose test (1-4): ").strip()
    
    if choice == '1':
        await test_acr_scraper()
    elif choice == '2':
        await test_clubwpt_scraper()
    elif choice == '3':
        await test_acr_scraper()
        print("\n" + "="*60 + "\n")
        await test_clubwpt_scraper()
    elif choice == '4':
        await test_data_conversion()
    
    # Always test conversion if we have data
    await test_data_conversion()
    
    print("\n" + "="*60)
    print("Test complete! Check generated JSON files for detailed data inspection.")


if __name__ == "__main__":
    asyncio.run(main())