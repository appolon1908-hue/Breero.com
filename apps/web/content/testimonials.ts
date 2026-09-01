export type Testimonial = {
  name: string;
  city: string;
  service: string;
  rating: number;
  quote: string;
  verified: boolean;
};
export const testimonials: Testimonial[] = [];
// Production renders no testimonial until a real customer quote is approved and marked verified.
