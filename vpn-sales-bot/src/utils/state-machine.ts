export type PaymentStatus = 'pending' | 'approved' | 'rejected';
export type OrderStatus =
  | 'pending'
  | 'waiting_payment'
  | 'paid'
  | 'provisioning'
  | 'completed'
  | 'cancelled'
  | 'failed';

export type ApprovalDecision = 'approve' | 'duplicate' | 'invalid';
export type ProvisionDecision = 'start' | 'retry' | 'skip' | 'conflict';

export function nextPaymentApproval(current: PaymentStatus): ApprovalDecision {
  if (current === 'pending') {
    return 'approve';
  }
  if (current === 'approved') {
    return 'duplicate';
  }
  return 'invalid';
}

export function nextPaymentRejection(current: PaymentStatus): ApprovalDecision {
  if (current === 'pending') {
    return 'approve';
  }
  if (current === 'rejected') {
    return 'duplicate';
  }
  return 'invalid';
}

export function canStartProvisioning(orderStatus: OrderStatus): ProvisionDecision {
  if (orderStatus === 'paid') {
    return 'start';
  }
  if (orderStatus === 'failed') {
    return 'retry';
  }
  if (orderStatus === 'completed') {
    return 'skip';
  }
  return 'conflict';
}
