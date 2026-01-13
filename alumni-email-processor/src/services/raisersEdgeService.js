import { config } from '../utils/config.js';
import { Logger } from '../utils/logger.js';

export class RaisersEdgeService {
  constructor() {
    this.apiKey = config.raisersEdge.apiKey;
    this.tenantId = config.raisersEdge.tenantId;
    this.baseUrl = config.raisersEdge.baseUrl;
    this.isConfigured = !!this.apiKey;

    if (!this.isConfigured) {
      Logger.warn('Raiser\'s Edge API key not configured. Staff assignment lookups will be skipped.');
    }
  }

  async findConstituentByEmail(email) {
    if (!this.isConfigured) {
      Logger.info('Raiser\'s Edge not configured, skipping constituent lookup');
      return null;
    }

    try {
      // Search for constituent by email
      const searchUrl = `${this.baseUrl}/constituent/v1/constituents/search`;

      const response = await fetch(searchUrl, {
        method: 'POST',
        headers: {
          'Bb-Api-Subscription-Key': this.apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          search_text: email,
          search_field: 'email_address',
        }),
      });

      if (!response.ok) {
        Logger.error(`Raiser's Edge API error: ${response.status} ${response.statusText}`);
        return null;
      }

      const data = await response.json();

      if (data.count > 0 && data.value && data.value.length > 0) {
        const constituent = data.value[0];
        Logger.info(`Found constituent in Raiser's Edge`, {
          id: constituent.id,
          name: constituent.name
        });
        return constituent;
      }

      Logger.info(`No constituent found for email: ${email}`);
      return null;
    } catch (error) {
      Logger.error('Error searching for constituent in Raiser\'s Edge', error);
      return null;
    }
  }

  async getConstituentStaffAssignments(constituentId) {
    if (!this.isConfigured) {
      return null;
    }

    try {
      // Get constituent's fundraiser assignments
      const url = `${this.baseUrl}/constituent/v1/constituents/${constituentId}/fundraisers`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Bb-Api-Subscription-Key': this.apiKey,
        },
      });

      if (!response.ok) {
        Logger.error(`Raiser's Edge API error: ${response.status} ${response.statusText}`);
        return null;
      }

      const data = await response.json();

      if (data.count > 0 && data.value && data.value.length > 0) {
        // Get the primary fundraiser/staff assignment
        const primaryAssignment = data.value.find(f => f.is_primary) || data.value[0];

        Logger.info(`Found staff assignment`, {
          staffId: primaryAssignment.fundraiser_id,
          isPrimary: primaryAssignment.is_primary
        });

        return await this.getFundraiserDetails(primaryAssignment.fundraiser_id);
      }

      Logger.info(`No staff assignments found for constituent ${constituentId}`);
      return null;
    } catch (error) {
      Logger.error('Error getting staff assignments from Raiser\'s Edge', error);
      return null;
    }
  }

  async getFundraiserDetails(fundraiserId) {
    if (!this.isConfigured) {
      return null;
    }

    try {
      const url = `${this.baseUrl}/fundraising/v1/fundraisers/${fundraiserId}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Bb-Api-Subscription-Key': this.apiKey,
        },
      });

      if (!response.ok) {
        Logger.error(`Raiser's Edge API error: ${response.status} ${response.statusText}`);
        return null;
      }

      const fundraiser = await response.json();

      Logger.info(`Found fundraiser details`, {
        id: fundraiser.id,
        name: fundraiser.name
      });

      return fundraiser.name || 'Unknown Staff';
    } catch (error) {
      Logger.error('Error getting fundraiser details from Raiser\'s Edge', error);
      return null;
    }
  }

  async getAssignedStaff(email) {
    if (!this.isConfigured) {
      return null;
    }

    try {
      Logger.info(`Looking up staff assignment for: ${email}`);

      const constituent = await this.findConstituentByEmail(email);

      if (!constituent) {
        return null;
      }

      const staffName = await this.getConstituentStaffAssignments(constituent.id);

      return staffName;
    } catch (error) {
      Logger.error('Error getting assigned staff', error);
      return null;
    }
  }
}
