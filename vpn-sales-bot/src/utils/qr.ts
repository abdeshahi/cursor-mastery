import QRCode from 'qrcode';

export interface QrDelivery {
  image: Buffer;
  caption: string;
  filename: string;
}

export async function createQrDelivery(input: {
  value: string;
  caption: string;
  filename: string;
}): Promise<QrDelivery> {
  const value = input.value.trim();
  if (value.length === 0) {
    throw new Error('QR value cannot be empty');
  }
  const image = await QRCode.toBuffer(value, {
    type: 'png',
    width: 512,
    margin: 2,
    errorCorrectionLevel: 'M',
  });
  return { image, caption: input.caption, filename: input.filename };
}
