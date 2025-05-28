import { X, Trash2, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { CartItem } from "@/lib/types";

interface CartSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  onRemoveItem: (productId: string) => void;
  onClearCart: () => void;
  onPlaceOrder: () => void;
}

export default function CartSidebar({
  isOpen,
  onClose,
  items,
  onRemoveItem,
  onClearCart,
  onPlaceOrder,
}: CartSidebarProps) {
  const totalAmount = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className={`fixed right-0 top-0 h-full w-96 bg-white shadow-2xl transform transition-transform z-50 ${
      isOpen ? 'translate-x-0' : 'translate-x-full'
    }`}>
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Shopping Cart</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="flex flex-col h-full">
        <ScrollArea className="flex-1 p-6">
          {items.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <ShoppingCart className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Your cart is empty</p>
              <p className="text-sm">Add products to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item) => (
                <div key={item.productId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800 text-sm line-clamp-2">{item.name}</h4>
                    <p className="text-gray-600 text-xs">₹{item.price.toLocaleString()} per {item.unit}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">×{item.quantity}</span>
                    <span className="text-sm font-bold text-primary">
                      ₹{(item.price * item.quantity).toLocaleString()}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-700 h-6 w-6 p-0"
                      onClick={() => onRemoveItem(item.productId)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <div className="border-t border-gray-200 p-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center text-lg font-semibold">
              <span>Total ({totalItems} items):</span>
              <span className="text-primary">₹{totalAmount.toLocaleString()}</span>
            </div>

            <Button
              className="w-full bg-primary hover:bg-blue-700"
              onClick={onPlaceOrder}
              disabled={items.length === 0}
            >
              Place Order
            </Button>

            <Button
              variant="outline"
              className="w-full"
              onClick={onClearCart}
              disabled={items.length === 0}
            >
              Clear Cart
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
