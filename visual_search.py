"""
Visual Search Service for VAESTA
Finds similar clothing items online based on recommended outfit images
"""

import requests
import os
from typing import List, Dict, Optional
from urllib.parse import quote


class VisualSearchService:
    """
    Service to find similar clothing products online using image-based search.
    Supports multiple search engines and shopping platforms.
    """
    
    def __init__(self, google_api_key: Optional[str] = None, google_cse_id: Optional[str] = None):
        """
        Initialize visual search service.
        
        Args:
            google_api_key: Google Custom Search API key
            google_cse_id: Google Custom Search Engine ID
        """
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY", "")
        self.google_cse_id = google_cse_id or os.getenv("GOOGLE_CSE_ID", "")
    
    def search_by_description(self, item_description: Dict, max_results: int = 3) -> List[Dict]:
        """
        Search for similar products using item description (fallback method).
        
        Args:
            item_description: Dictionary with category, color, pattern info
            max_results: Maximum number of results to return
            
        Returns:
            List of product dictionaries with name, price, url, image
        """
        # Build search query from item attributes
        category = item_description.get('category', 'clothing')
        color = item_description.get('color', '')
        pattern = item_description.get('pattern', '')
        
        # Create search terms
        search_terms = [category]
        if color and color not in ['not specified', 'various']:
            search_terms.append(color)
        if pattern and 'pure color' not in pattern.lower():
            search_terms.append(pattern.split('(')[0].strip())
        
        query = ' '.join(search_terms) + ' buy online'
        
        # Try Google Shopping search if API keys are available
        if self.google_api_key and self.google_cse_id:
            return self._google_shopping_search(query, max_results)
        else:
            # Return mock results for demonstration
            return self._generate_mock_results(item_description, max_results)
    
    def _google_shopping_search(self, query: str, max_results: int) -> List[Dict]:
        """
        Search Google Shopping API for products.
        
        Args:
            query: Search query string
            max_results: Maximum results
            
        Returns:
            List of product results
        """
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'searchType': 'image',
                'num': max_results,
                'safe': 'active',
                'fileType': 'jpg,png'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', [])[:max_results]:
                results.append({
                    'name': item.get('title', 'Product'),
                    'price': self._extract_price(item.get('snippet', '')),
                    'url': item.get('link', '#'),
                    'image': item.get('image', {}).get('thumbnailLink', ''),
                    'source': 'Google Shopping'
                })
            
            return results if results else self._generate_mock_results({'category': query}, max_results)
            
        except Exception as e:
            print(f"⚠️ Google Shopping search error: {e}")
            return self._generate_mock_results({'category': query}, max_results)
    
    def _extract_price(self, text: str) -> str:
        """Extract price from text snippet."""
        import re
        price_pattern = r'\$[\d,]+(?:\.\d{2})?'
        match = re.search(price_pattern, text)
        return match.group(0) if match else "$$$"
    
    def _generate_mock_results(self, item_description: Dict, max_results: int) -> List[Dict]:
        """
        Generate mock shopping results based on item description.
        
        Args:
            item_description: Item attributes
            max_results: Number of results
            
        Returns:
            List of mock product results with actual image URLs
        """
        category = item_description.get('category', 'clothing').title()
        color = item_description.get('color', 'Classic')
        
        # Generate realistic mock products with actual placeholder images
        base_products = {
            'jacket': [
                {'name': 'Premium Denim Jacket', 'price': '$89', 'store': 'Zara', 
                 'image': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=300&h=400&fit=crop'},
                {'name': 'Classic Bomber Jacket', 'price': '$125', 'store': 'H&M',
                 'image': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=300&h=400&fit=crop'},
                {'name': 'Lightweight Spring Jacket', 'price': '$75', 'store': 'Uniqlo',
                 'image': 'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=300&h=400&fit=crop'}
            ],
            'coat': [
                {'name': 'Wool Blend Overcoat', 'price': '$180', 'store': 'Mango',
                 'image': 'https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=300&h=400&fit=crop'},
                {'name': 'Trench Coat Classic', 'price': '$145', 'store': 'Gap',
                 'image': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=300&h=400&fit=crop'},
                {'name': 'Winter Long Coat', 'price': '$210', 'store': 'Zara',
                 'image': 'https://images.unsplash.com/photo-1544923246-77307d119b12?w=300&h=400&fit=crop'}
            ],
            't-shirt': [
                {'name': 'Cotton Basic Tee', 'price': '$25', 'store': 'Uniqlo',
                 'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=300&h=400&fit=crop'},
                {'name': 'Premium T-Shirt', 'price': '$35', 'store': 'Everlane',
                 'image': 'https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=300&h=400&fit=crop'},
                {'name': 'Organic Cotton Tee', 'price': '$30', 'store': 'H&M',
                 'image': 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=300&h=400&fit=crop'}
            ],
            'sweater': [
                {'name': 'Cashmere Blend Sweater', 'price': '$95', 'store': 'J.Crew',
                 'image': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=300&h=400&fit=crop'},
                {'name': 'Wool Pullover', 'price': '$78', 'store': 'Gap',
                 'image': 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=300&h=400&fit=crop'},
                {'name': 'Knit Cardigan', 'price': '$65', 'store': 'Uniqlo',
                 'image': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=300&h=400&fit=crop'}
            ],
            'jeans': [
                {'name': 'Slim Fit Jeans', 'price': '$68', 'store': "Levi's",
                 'image': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=300&h=400&fit=crop'},
                {'name': 'High-Rise Denim', 'price': '$85', 'store': 'Madewell',
                 'image': 'https://images.unsplash.com/photo-1582418702059-97ebafb35d09?w=300&h=400&fit=crop'},
                {'name': 'Straight Leg Jeans', 'price': '$75', 'store': 'Gap',
                 'image': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=300&h=400&fit=crop'}
            ],
            'dress': [
                {'name': 'Midi Dress', 'price': '$95', 'store': 'Zara',
                 'image': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=300&h=400&fit=crop'},
                {'name': 'Casual Day Dress', 'price': '$65', 'store': 'H&M',
                 'image': 'https://images.unsplash.com/photo-1612423284934-2850a4ea6b0f?w=300&h=400&fit=crop'},
                {'name': 'Evening Dress', 'price': '$140', 'store': 'Mango',
                 'image': 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=300&h=400&fit=crop'}
            ]
        }
        
        # Find matching category or use default
        cat_key = category.lower()
        for key in base_products:
            if key in cat_key or cat_key in key:
                products = base_products[key]
                break
        else:
            products = base_products['t-shirt']
        
        # Add color information to product names
        results = []
        for i, product in enumerate(products[:max_results]):
            color_prefix = f"{color.title()} " if color and i == 0 else ""
            results.append({
                'name': f"{color_prefix}{product['name']}",
                'price': product['price'],
                'url': f"https://www.google.com/search?q={quote(product['name'])}+{quote(product['store'])}",
                'image': product['image'],
                'source': product['store'],
                'match': f"{95 - i * 3}%"
            })
        
        return results
    
    def find_similar_from_outfit(self, recommendation: Dict) -> Dict[str, List[Dict]]:
        """
        Find similar products for each item in the recommended outfit.
        
        Args:
            recommendation: Outfit recommendation dictionary
            
        Returns:
            Dictionary mapping item type to list of similar products
        """
        results = {}
        
        if recommendation.get('outfit_type') == 'Dress':
            dress = recommendation.get('dress', {})
            results['dress'] = self.search_by_description(dress, max_results=3)
        
        elif recommendation.get('outfit_type') == 'Layered':
            # Search for each layer
            if recommendation.get('outer'):
                results['outer'] = self.search_by_description(recommendation['outer'], max_results=3)
            
            if recommendation.get('top'):
                results['top'] = self.search_by_description(recommendation['top'], max_results=3)
            
            if recommendation.get('bottom'):
                results['bottom'] = self.search_by_description(recommendation['bottom'], max_results=3)
        
        return results


# Convenience function
def find_shopping_options(recommendation: Dict) -> Dict[str, List[Dict]]:
    """
    Quick function to find shopping options for a recommendation.
    
    Args:
        recommendation: Outfit recommendation dictionary
        
    Returns:
        Dictionary of shopping results by item type
    """
    service = VisualSearchService()
    return service.find_similar_from_outfit(recommendation)
