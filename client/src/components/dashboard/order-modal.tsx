import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";

interface OrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  orderId: string;
  totalAmount: number;
}

export default function OrderModal({ isOpen, onClose, orderId, totalAmount }: OrderModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <div className="text-center py-4">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-gray-800 mb-2">Order Placed Successfully!</h3>
          <p className="text-gray-600 mb-6">Your order has been submitted and will be processed shortly.</p>
          
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600">Order ID</p>
            <p className="font-mono text-lg font-semibold">{orderId}</p>
            <p className="text-sm text-gray-600 mt-2">Total Amount</p>
            <p className="text-xl font-bold text-primary">₹{totalAmount.toLocaleString()}</p>
          </div>
          
          <div className="space-y-3">
            <Button 
              className="w-full bg-primary hover:bg-blue-700" 
              onClick={onClose}
            >
              Continue Shopping
            </Button>
            <Button 
              variant="outline" 
              className="w-full"
              onClick={() => {
                onClose();
                // In real implementation, this would navigate to orders page
                alert('Order history feature would be implemented here');
              }}
            >
              View All Orders
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
