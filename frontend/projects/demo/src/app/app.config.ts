import { APP_INITIALIZER, ApplicationConfig } from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import { PrimeNGConfig } from 'primeng/api';

import { QUERY_BUILDER_PT } from '@query-builder/ui';

function configurePrimeNg(config: PrimeNGConfig): () => void {
  return () => {
    config.ripple = false;

    const passThroughConfig = config as PrimeNGConfig & {
      pt?: typeof QUERY_BUILDER_PT;
      unstyled?: boolean;
    };

    passThroughConfig.unstyled = true;
    passThroughConfig.pt = QUERY_BUILDER_PT;
  };
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideAnimations(),
    {
      provide: APP_INITIALIZER,
      useFactory: configurePrimeNg,
      deps: [PrimeNGConfig],
      multi: true
    }
  ]
};
