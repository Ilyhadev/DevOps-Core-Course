export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

function json(data: unknown, status = 200): Response {
  return Response.json(data, { status });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Basic observability marker for wrangler tail / dashboard logs.
    console.log("request", {
      path,
      method: request.method,
      colo: request.cf?.colo,
      country: request.cf?.country
    });

    if (path === "/health") {
      return json({
        status: "ok",
        app: env.APP_NAME,
        timestamp: new Date().toISOString()
      });
    }

    if (path === "/") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        runtime: "edge",
        timestamp: new Date().toISOString(),
        endpoints: ["/", "/health", "/edge", "/counter", "/config"]
      });
    }

    if (path === "/edge") {
      return json({
        colo: request.cf?.colo ?? null,
        country: request.cf?.country ?? null,
        city: request.cf?.city ?? null,
        asn: request.cf?.asn ?? null,
        httpProtocol: request.cf?.httpProtocol ?? null,
        tlsVersion: request.cf?.tlsVersion ?? null,
        userAgent: request.headers.get("user-agent")
      });
    }

    if (path === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));

      return json({
        key: "visits",
        visits,
        persisted: true
      });
    }

    if (path === "/config") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        secretsPresent: {
          apiToken: Boolean(env.API_TOKEN),
          adminEmail: Boolean(env.ADMIN_EMAIL)
        },
        // Do not expose secret values themselves.
        secretPreview: {
          adminEmailDomain: env.ADMIN_EMAIL?.split("@")[1] ?? null
        }
      });
    }

    return json(
      {
        error: "Not Found",
        path
      },
      404
    );
  }
};
