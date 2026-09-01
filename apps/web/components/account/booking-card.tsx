import { ArrowRightIcon, CalendarIcon, Card, ClockIcon, Price } from "@breero/ui";
import type { CustomerBooking } from "@/lib/customer/data";
import { formatDate } from "@/lib/customer/data";
import { BookingStatus } from "./booking-status";

export function BookingCard({ booking }: { booking: CustomerBooking }) {
  return (
    <a className="booking-card-link" href={`/account/bookings/${booking.id}`}>
      <Card interactive className="booking-card">
        <div className="booking-card__top">
          <span className="booking-card__category">{booking.category.slice(0, 1)}</span>
          <div>
            <small>{booking.reference}</small>
            <h2>{booking.service}</h2>
          </div>
          <BookingStatus status={booking.status} />
        </div>
        <div className="booking-card__meta">
          <span>
            <CalendarIcon />
            {formatDate(booking.window_start, { weekday: "short", day: "numeric", month: "short" })}
          </span>
          <span>
            <ClockIcon />
            {new Intl.DateTimeFormat("en-GB", {
              hour: "2-digit",
              minute: "2-digit",
              timeZone: "UTC",
            }).format(new Date(booking.window_start))}
            –
            {new Intl.DateTimeFormat("en-GB", {
              hour: "2-digit",
              minute: "2-digit",
              timeZone: "UTC",
            }).format(new Date(booking.window_end))}
          </span>
          <Price amount={Number(booking.total_amount)} currency={booking.currency} />
        </div>
        <div className="booking-card__footer">
          <span>{booking.address}</span>
          <strong>
            View details <ArrowRightIcon />
          </strong>
        </div>
      </Card>
    </a>
  );
}
