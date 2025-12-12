"""
Visual Search Service for VAESTA
Finds similar clothing items online based on recommended outfit images
"""

import requests
import os
import random
import hashlib
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
    
    def search_by_description(self, item_description: Dict, max_results: int = 3, gender: Optional[str] = None, recommended_item: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar products using item description (fallback method).
        
        Args:
            item_description: Dictionary with category, color, pattern info
            max_results: Maximum number of results to return
            gender: User's gender ("Male" or "Female") for gender-specific results
            recommended_item: The actual recommended item (to use its image)
            
        Returns:
            List of product dictionaries with name, price, url, image
        """
        # Build search query from item attributes
        category = item_description.get('category', 'clothing')
        color = item_description.get('color', '')
        pattern = item_description.get('pattern', '')
        
        # Normalize category name (handle variations)
        category = str(category).lower().strip()
        
        # Add gender to search terms if provided
        search_terms = [category]
        if gender:
            search_terms.append(gender.lower())
        if color and color not in ['not specified', 'various', '']:
            search_terms.append(color)
        if pattern and 'pure color' not in pattern.lower():
            search_terms.append(pattern.split('(')[0].strip())
        
        query = ' '.join(search_terms) + ' buy online'
        
        # Try Google Shopping search if API keys are available
        if self.google_api_key and self.google_cse_id:
            return self._google_shopping_search(query, max_results)
        else:
            # Return mock results for demonstration
            # Pass normalized category, gender, and recommended item to ensure proper matching
            item_description_normalized = item_description.copy()
            item_description_normalized['category'] = category
            item_description_normalized['gender'] = gender
            item_description_normalized['recommended_item'] = recommended_item
            return self._generate_mock_results(item_description_normalized, max_results)
    
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
            item_description: Item attributes with category, color, gender, etc.
            max_results: Number of results
            
        Returns:
            List of mock product results with actual image URLs
        """
        # Get category and normalize it (keep lowercase for matching)
        category_raw = item_description.get('category', 'clothing')
        category_lower = str(category_raw).lower().strip()
        color = item_description.get('color', '')
        gender = item_description.get('gender', '')
        
        # Create a seed based on category, color, and gender for consistent but varied results
        # This ensures same items get same results, but different items get different results
        seed_string = f"{category_lower}_{color}_{gender}_{item_description.get('warmth_score', 3)}"
        seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Generate realistic mock products with actual placeholder images
        # Products are organized by exact category match
        # Note: Images are from Unsplash and may not match exact colors, but names will be accurate
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
            'hoodie': [
                {'name': 'Classic Hoodie', 'price': '$65', 'store': 'Uniqlo',
                 'image': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=300&h=400&fit=crop'},
                {'name': 'Premium Zip Hoodie', 'price': '$85', 'store': 'H&M',
                 'image': 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=300&h=400&fit=crop'},
                {'name': 'Oversized Hoodie', 'price': '$75', 'store': 'Zara',
                 'image': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=300&h=400&fit=crop'}
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
            'trousers': [
                {'name': 'Classic Chinos', 'price': '$60', 'store': 'Gap',
                 'image': 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=300&h=400&fit=crop'},
                {'name': 'Tailored Trousers', 'price': '$85', 'store': 'Zara',
                 'image': 'https://images.unsplash.com/photo-1594938291221-94f313391970?w=300&h=400&fit=crop'},
                {'name': 'Smart Pants', 'price': '$70', 'store': 'H&M',
                 'image': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=300&h=400&fit=crop'}
            ],
            'shorts': [
                {'name': 'Cargo Shorts', 'price': '$45', 'store': 'Uniqlo',
                 'image': 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=300&h=400&fit=crop'},
                {'name': 'Athletic Shorts', 'price': '$35', 'store': 'Nike',
                 'image': 'https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=300&h=400&fit=crop'},
                {'name': 'Casual Shorts', 'price': '$40', 'store': 'H&M',
                 'image': 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=300&h=400&fit=crop'}
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
        
        # Find matching category - prioritize exact matches
        # Use the normalized lowercase category
        cat_key = category_lower
        matching_products = None
        
        # First, try exact category match
        if cat_key in base_products:
            matching_products = base_products[cat_key]
        else:
            # Try partial matches (e.g., "button-up shirt" -> "t-shirt")
            for key in base_products:
                if key in cat_key or cat_key in key:
                    matching_products = base_products[key]
                    break
        
        # Fallback to similar categories
        if not matching_products:
            if 'shirt' in cat_key or 'blouse' in cat_key or 'polo' in cat_key:
                matching_products = base_products.get('t-shirt', base_products['t-shirt'])
            elif 'sweater' in cat_key or 'pullover' in cat_key or 'cardigan' in cat_key:
                matching_products = base_products.get('sweater', base_products['sweater'])
            elif 'jacket' in cat_key:
                matching_products = base_products.get('jacket', base_products['jacket'])
            elif 'coat' in cat_key or 'overcoat' in cat_key:
                matching_products = base_products.get('coat', base_products['coat'])
            elif 'hoodie' in cat_key:
                matching_products = base_products.get('hoodie', base_products['hoodie'])
            elif 'jean' in cat_key or 'denim' in cat_key:
                matching_products = base_products.get('jeans', base_products['jeans'])
            elif 'trouser' in cat_key or 'pant' in cat_key or 'chino' in cat_key:
                matching_products = base_products.get('trousers', base_products.get('jeans', base_products['jeans']))
            elif 'short' in cat_key:
                matching_products = base_products.get('shorts', base_products.get('jeans', base_products['jeans']))
            elif 'dress' in cat_key:
                matching_products = base_products.get('dress', base_products['dress'])
            else:
                matching_products = base_products['t-shirt']
        
        # Shuffle products to add variety (but keep seed-based consistency)
        products = matching_products.copy()
        random.shuffle(products)
        
        # Clean and format color name
        color_clean = ""
        if color and color not in ['not specified', 'various', '', 'none']:
            color_clean = color.strip().title()
        
        # Get the recommended item's image if available (for first result)
        recommended_item = item_description.get('recommended_item', {})
        recommended_image = recommended_item.get('image_link', '') if recommended_item else ''
        
        # Generate results with proper color and gender matching
        results = []
        for i, product in enumerate(products[:max_results]):
            # Build product name with color and gender context
            product_name_parts = []
            
            # Always include color in product name to match recommendation (if available)
            if color_clean:
                product_name_parts.append(color_clean)
            
            # Add gender-specific descriptor if gender is provided
            if gender:
                gender_lower = str(gender).lower().strip()
                if gender_lower == 'male':
                    # For male items, we can add "Men's" prefix for clarity
                    if i == 0:  # Only for first result to avoid repetition
                        product_name_parts.append("Men's")
                elif gender_lower == 'female':
                    if i == 0:  # Only for first result to avoid repetition
                        product_name_parts.append("Women's")
            
            # Add the base product name
            product_name_parts.append(product['name'])
            
            # Combine into final product name
            product_name = ' '.join(product_name_parts)
            
            # Use recommended item's image for first result if available
            # This ensures the image matches the actual recommendation
            product_image = product['image']
            if i == 0 and recommended_image:
                # Use the actual recommended item's image
                product_image = recommended_image
                # Note: This might be a local path, so we'll handle it in the display code
            
            # Vary match percentage slightly
            base_match = 95 - i * 3
            match_variation = random.randint(-2, 2)
            match_score = max(85, min(98, base_match + match_variation))
            
            # Build search query with gender for better results
            search_query = product_name
            if gender:
                search_query += f" {gender.lower()}"
            
            results.append({
                'name': product_name,
                'price': product['price'],
                'url': f"https://www.google.com/search?q={quote(search_query)}+{quote(product['store'])}",
                'image': product_image,
                'source': product['store'],
                'match': f"{match_score}%",
                'is_recommended_image': (i == 0 and recommended_image != '')  # Flag for first image
            })
        
        return results
    
    def find_similar_from_outfit(self, recommendation: Dict, gender: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Find similar products for each item in the recommended outfit.
        
        Args:
            recommendation: Outfit recommendation dictionary
            gender: User's gender ("Male" or "Female") for gender-specific results
            
        Returns:
            Dictionary mapping item type to list of similar products
        """
        results = {}
        
        if recommendation.get('outfit_type') == 'Dress':
            dress = recommendation.get('dress', {})
            # Pass the actual recommended item so we can use its image
            results['dress'] = self.search_by_description(dress, max_results=3, gender=gender, recommended_item=dress)
        
        elif recommendation.get('outfit_type') == 'Layered':
            # Search for each layer
            if recommendation.get('outer'):
                results['outer'] = self.search_by_description(
                    recommendation['outer'], max_results=3, gender=gender, 
                    recommended_item=recommendation['outer']
                )
            
            if recommendation.get('top'):
                results['top'] = self.search_by_description(
                    recommendation['top'], max_results=3, gender=gender,
                    recommended_item=recommendation['top']
                )
            
            if recommendation.get('bottom'):
                results['bottom'] = self.search_by_description(
                    recommendation['bottom'], max_results=3, gender=gender,
                    recommended_item=recommendation['bottom']
                )
        
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
