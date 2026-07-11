import { Badge } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

interface Health {
  status: string;
  version: string;
}

export function ApiHealthBadge() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<Health>("/health"),
  });

  if (data) {
    return (
      <Badge color="green" variant="light">
        ✓ API · v{data.version}
      </Badge>
    );
  }

  if (isError) {
    return (
      <Badge color="red" variant="light">
        API unreachable
      </Badge>
    );
  }

  return (
    <Badge color="gray" variant="light">
      connecting…
    </Badge>
  );
}
