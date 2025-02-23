from typing import List, Dict, Any, Optional
from trello import TrelloClient
import logging

logger = logging.getLogger(__name__)

class TrelloServices:
    def __init__(self, access_token: str):
        """Initialize with access token from frontend"""
        self.client = TrelloClient(token=access_token)

    def get_boards(self) -> List[Dict[str, Any]]:
        """Get all boards"""
        try:
            boards = self.client.list_boards()
            return [
                {
                    'id': board.id,
                    'name': board.name,
                    'description': board.description,
                    'url': board.url,
                    'closed': board.closed
                } for board in boards
            ]
        except Exception as e:
            logger.error(f"Error fetching boards: {str(e)}")
            raise

    def get_lists(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all lists in a board"""
        try:
            board = self.client.get_board(board_id)
            lists = board.list_lists()
            return [
                {
                    'id': lst.id,
                    'name': lst.name,
                    'closed': lst.closed,
                    'pos': lst.pos
                } for lst in lists
            ]
        except Exception as e:
            logger.error(f"Error fetching lists: {str(e)}")
            raise

    def get_cards(self, list_id: str) -> List[Dict[str, Any]]:
        """Get all cards in a list"""
        try:
            lst = self.client.get_list(list_id)
            cards = lst.list_cards()
            return [
                {
                    'id': card.id,
                    'name': card.name,
                    'description': card.description,
                    'due': card.due_date,
                    'url': card.url,
                    'closed': card.closed,
                    'labels': [{'name': label.name, 'color': label.color} for label in card.labels]
                } for card in cards
            ]
        except Exception as e:
            logger.error(f"Error fetching cards: {str(e)}")
            raise

    def create_card(self,
                   list_id: str,
                   name: str,
                   description: Optional[str] = None,
                   due: Optional[str] = None,
                   position: str = 'bottom') -> Dict[str, Any]:
        """Create a new card"""
        try:
            lst = self.client.get_list(list_id)
            card = lst.add_card(
                name=name,
                desc=description,
                due=due,
                position=position
            )
            return {
                'id': card.id,
                'name': card.name,
                'description': card.description,
                'due': card.due_date,
                'url': card.url
            }
        except Exception as e:
            logger.error(f"Error creating card: {str(e)}")
            raise

    def update_card(self,
                   card_id: str,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   due: Optional[str] = None,
                   closed: Optional[bool] = None) -> Dict[str, Any]:
        """Update an existing card"""
        try:
            card = self.client.get_card(card_id)
            if name is not None:
                card.set_name(name)
            if description is not None:
                card.set_description(description)
            if due is not None:
                card.set_due(due)
            if closed is not None:
                if closed:
                    card.set_closed(True)
                else:
                    card.set_closed(False)

            return {
                'id': card.id,
                'name': card.name,
                'description': card.description,
                'due': card.due_date,
                'url': card.url,
                'closed': card.closed
            }
        except Exception as e:
            logger.error(f"Error updating card: {str(e)}")
            raise

    def delete_card(self, card_id: str) -> None:
        """Delete a card"""
        try:
            card = self.client.get_card(card_id)
            card.delete()
        except Exception as e:
            logger.error(f"Error deleting card: {str(e)}")
            raise

    def create_list(self,
                   board_id: str,
                   name: str,
                   position: str = 'bottom') -> Dict[str, Any]:
        """Create a new list"""
        try:
            board = self.client.get_board(board_id)
            lst = board.add_list(name=name, pos=position)
            return {
                'id': lst.id,
                'name': lst.name,
                'closed': lst.closed,
                'pos': lst.pos
            }
        except Exception as e:
            logger.error(f"Error creating list: {str(e)}")
            raise

    def create_board(self,
                    name: str,
                    description: Optional[str] = None,
                    default_lists: bool = True) -> Dict[str, Any]:
        """Create a new board"""
        try:
            board = self.client.add_board(
                board_name=name,
                default_lists=default_lists
            )
            if description:
                board.set_description(description)
            
            return {
                'id': board.id,
                'name': board.name,
                'description': board.description,
                'url': board.url,
                'closed': board.closed
            }
        except Exception as e:
            logger.error(f"Error creating board: {str(e)}")
            raise 