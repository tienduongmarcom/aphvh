import { Plugin } from '@nocobase/client';
import models from './models';

export class PluginKhoClient extends Plugin {
  async load() {
    this.flowEngine.registerModels(models);
  }
}

export default PluginKhoClient;
