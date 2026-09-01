import { Card, Grid, Skeleton, Stack } from "@breero/ui";
export default function AccountLoading() {
  return (
    <div aria-label="Loading account" role="status">
      <Stack gap="sm">
        <Skeleton width="35%" height={44} />
        <Skeleton width="55%" />
      </Stack>
      <Grid columns={2} gap="lg" className="account-loading-grid">
        {[1, 2, 3, 4].map((item) => (
          <Card key={item}>
            <Stack gap="md">
              <Skeleton width={48} height={48} rounded />
              <Skeleton width="70%" height={24} />
              <Skeleton width="100%" />
              <Skeleton width="82%" />
            </Stack>
          </Card>
        ))}
      </Grid>
      <span className="br-sr-only">Loading your account</span>
    </div>
  );
}
