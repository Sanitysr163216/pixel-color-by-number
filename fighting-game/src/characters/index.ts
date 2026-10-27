import { compileCharacter, type CompiledCharacter } from './compile';
import { shoto } from './shoto/character';

export const CHARACTERS: Record<string, CompiledCharacter> = {
  shoto: compileCharacter(shoto),
};
