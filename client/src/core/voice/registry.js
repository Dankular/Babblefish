// Voice Registry - IndexedDB storage for speaker voice references

const DB_NAME = 'babblefish_voices';
const DB_VERSION = 1;
const STORE_NAME = 'voice_references';

/**
 * Voice Registry
 *
 * Manages persistent storage of voice references in IndexedDB.
 * Each voice reference is stored with speaker metadata.
 */
export class VoiceRegistry {
  constructor() {
    this.db = null;
  }

  /**
   * Initialize IndexedDB
   * @returns {Promise<void>}
   */
  async initialize() {
    if (this.db) {
      console.log('[VoiceRegistry] Already initialized');
      return;
    }

    return new Promise((resolve, reject) => {
      console.log('[VoiceRegistry] Initializing IndexedDB...');

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to open IndexedDB:', request.error);
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('[VoiceRegistry] IndexedDB initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        console.log('[VoiceRegistry] Upgrading IndexedDB schema...');
        const db = event.target.result;

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const objectStore = db.createObjectStore(STORE_NAME, { keyPath: 'speaker_id' });
          objectStore.createIndex('room_id', 'room_id', { unique: false });
          objectStore.createIndex('created_at', 'created_at', { unique: false });
          console.log('[VoiceRegistry] Object store created');
        }
      };
    });
  }

  /**
   * Store voice reference
   * @param {string} speakerId - Unique speaker identifier
   * @param {Object} voiceData - Voice reference data
   * @returns {Promise<void>}
   */
  async storeVoiceReference(speakerId, voiceData) {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    console.log(`[VoiceRegistry] Storing voice reference for speaker: ${speakerId}`);

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);

      const record = {
        speaker_id: speakerId,
        voice_reference: voiceData.audioData,
        sample_rate: voiceData.sampleRate,
        duration: voiceData.duration,
        samples: voiceData.samples,
        room_id: voiceData.roomId || null,
        speaker_name: voiceData.speakerName || null,
        language: voiceData.language || null,
        created_at: Date.now(),
        updated_at: Date.now(),
      };

      const request = store.put(record);

      request.onsuccess = () => {
        console.log(`[VoiceRegistry] Voice reference stored for ${speakerId}`);
        resolve();
      };

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to store voice reference:', request.error);
        reject(new Error('Failed to store voice reference'));
      };
    });
  }

  /**
   * Get voice reference
   * @param {string} speakerId - Speaker identifier
   * @returns {Promise<Object|null>} Voice reference data or null if not found
   */
  async getVoiceReference(speakerId) {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(speakerId);

      request.onsuccess = () => {
        const result = request.result;
        if (result) {
          console.log(`[VoiceRegistry] Retrieved voice reference for ${speakerId}`);
        } else {
          console.log(`[VoiceRegistry] No voice reference found for ${speakerId}`);
        }
        resolve(result || null);
      };

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to get voice reference:', request.error);
        reject(new Error('Failed to get voice reference'));
      };
    });
  }

  /**
   * Check if voice reference exists
   * @param {string} speakerId - Speaker identifier
   * @returns {Promise<boolean>}
   */
  async hasVoiceReference(speakerId) {
    const reference = await this.getVoiceReference(speakerId);
    return reference !== null;
  }

  /**
   * Get all voice references for a room
   * @param {string} roomId - Room identifier
   * @returns {Promise<Object[]>} Array of voice references
   */
  async getVoiceReferencesForRoom(roomId) {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const index = store.index('room_id');
      const request = index.getAll(roomId);

      request.onsuccess = () => {
        console.log(`[VoiceRegistry] Retrieved ${request.result.length} voice references for room ${roomId}`);
        resolve(request.result);
      };

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to get room voice references:', request.error);
        reject(new Error('Failed to get room voice references'));
      };
    });
  }

  /**
   * Get all voice references
   * @returns {Promise<Object[]>} Array of all voice references
   */
  async getAllVoiceReferences() {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        console.log(`[VoiceRegistry] Retrieved ${request.result.length} voice references`);
        resolve(request.result);
      };

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to get all voice references:', request.error);
        reject(new Error('Failed to get all voice references'));
      };
    });
  }

  /**
   * Delete voice reference
   * @param {string} speakerId - Speaker identifier
   * @returns {Promise<void>}
   */
  async deleteVoiceReference(speakerId) {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    console.log(`[VoiceRegistry] Deleting voice reference for ${speakerId}`);

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(speakerId);

      request.onsuccess = () => {
        console.log(`[VoiceRegistry] Voice reference deleted for ${speakerId}`);
        resolve();
      };

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to delete voice reference:', request.error);
        reject(new Error('Failed to delete voice reference'));
      };
    });
  }

  /**
   * Clear all voice references
   * @returns {Promise<void>}
   */
  async clearAll() {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    console.log('[VoiceRegistry] Clearing all voice references...');

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => {
        console.log('[VoiceRegistry] All voice references cleared');
        resolve();
      };

      request.onerror = () => {
        console.error('[VoiceRegistry] Failed to clear voice references:', request.error);
        reject(new Error('Failed to clear voice references'));
      };
    });
  }

  /**
   * Get storage statistics
   * @returns {Promise<Object>} Storage stats
   */
  async getStats() {
    if (!this.db) {
      throw new Error('VoiceRegistry not initialized');
    }

    const allReferences = await this.getAllVoiceReferences();

    let totalSize = 0;
    for (const ref of allReferences) {
      if (ref.voice_reference) {
        totalSize += ref.voice_reference.byteLength;
      }
    }

    return {
      count: allReferences.length,
      totalSize,
      totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
    };
  }

  /**
   * Close database connection
   */
  close() {
    if (this.db) {
      console.log('[VoiceRegistry] Closing IndexedDB connection');
      this.db.close();
      this.db = null;
    }
  }
}

/**
 * Global singleton instance
 */
let globalRegistry = null;

/**
 * Get global voice registry instance
 * @returns {Promise<VoiceRegistry>}
 */
export async function getVoiceRegistry() {
  if (!globalRegistry) {
    globalRegistry = new VoiceRegistry();
    await globalRegistry.initialize();
  }
  return globalRegistry;
}
