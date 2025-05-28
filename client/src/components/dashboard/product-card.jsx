import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Minus, Plus, ShoppingCart } from "lucide-react";
import { getStockStatusColor, getStockStatusText } from "@/lib/types";

export default function ProductCard({ product, onAddToCart }) {
  const [quantity, setQuantity] = useState(0);

  const handleDecrease = () => {
    if (quantity > 0) {
      setQuantity(quantity - 1);
    }
  };

  const handleIncrease = () => {
    setQuantity(quantity + 1);
  };

  const handleAddToCart = () => {
    if (quantity > 0) {
      onAddToCart(product.id, quantity);
      setQuantity(0);
    }
  };

  const price = parseFloat(product.price);

  return (
    <Card className="h-full hover:shadow-lg transition-shadow">
      <div className="aspect-video w-full overflow-hidden rounded-t-lg">
        <img 
          src={product.imageUrl || "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&h=200"} 
          alt={product.name}
          className="w-full h-full object-cover"
        />
      </div>
      
      <CardContent className="p-4">
        <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2">{product.name}</h3>
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">{product.description}</p>
        
        <div className="flex items-center justify-between mb-4">
          <span className="text-lg font-bold text-primary">₹{price.toLocaleString()}/{product.unit}</span>
          <Badge className={getStockStatusColor(product.stockStatus)}>
            {getStockStatusText(product.stockStatus)}
          </Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              className="w-8 h-8 rounded-full p-0"
              onClick={handleDecrease}
              disabled={quantity === 0}
            >
              <Minus className="h-3 w-3" />
            </Button>
            
            <span className="font-semibold text-gray-800 min-w-8 text-center">
              {quantity}
            </span>
            
            <Button
              size="sm"
              className="w-8 h-8 rounded-full p-0 bg-primary hover:bg-blue-700"
              onClick={handleIncrease}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>
          
          <Button
            size="sm"
            className="bg-secondary hover:bg-green-700"
            onClick={handleAddToCart}
            disabled={quantity === 0 || product.stockStatus === "out_of_stock"}
          >
            <ShoppingCart className="h-3 w-3 mr-1" />
            Add to Cart
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}