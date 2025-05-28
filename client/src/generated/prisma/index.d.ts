
/**
 * Client
**/

import * as runtime from './runtime/library.js';
import $Types = runtime.Types // general types
import $Public = runtime.Types.Public
import $Utils = runtime.Types.Utils
import $Extensions = runtime.Types.Extensions
import $Result = runtime.Types.Result

export type PrismaPromise<T> = $Public.PrismaPromise<T>


/**
 * Model User
 * 
 */
export type User = $Result.DefaultSelection<Prisma.$UserPayload>
/**
 * Model MandiLatLong
 * 
 */
export type MandiLatLong = $Result.DefaultSelection<Prisma.$MandiLatLongPayload>
/**
 * Model Truck
 * 
 */
export type Truck = $Result.DefaultSelection<Prisma.$TruckPayload>
/**
 * Model VoiceResponse
 * 
 */
export type VoiceResponse = $Result.DefaultSelection<Prisma.$VoiceResponsePayload>

/**
 * ##  Prisma Client ʲˢ
 *
 * Type-safe database client for TypeScript & Node.js
 * @example
 * ```
 * const prisma = new PrismaClient()
 * // Fetch zero or more Users
 * const users = await prisma.user.findMany()
 * ```
 *
 *
 * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
 */
export class PrismaClient<
  ClientOptions extends Prisma.PrismaClientOptions = Prisma.PrismaClientOptions,
  U = 'log' extends keyof ClientOptions ? ClientOptions['log'] extends Array<Prisma.LogLevel | Prisma.LogDefinition> ? Prisma.GetEvents<ClientOptions['log']> : never : never,
  ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs
> {
  [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['other'] }

    /**
   * ##  Prisma Client ʲˢ
   *
   * Type-safe database client for TypeScript & Node.js
   * @example
   * ```
   * const prisma = new PrismaClient()
   * // Fetch zero or more Users
   * const users = await prisma.user.findMany()
   * ```
   *
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
   */

  constructor(optionsArg ?: Prisma.Subset<ClientOptions, Prisma.PrismaClientOptions>);
  $on<V extends U>(eventType: V, callback: (event: V extends 'query' ? Prisma.QueryEvent : Prisma.LogEvent) => void): PrismaClient;

  /**
   * Connect with the database
   */
  $connect(): $Utils.JsPromise<void>;

  /**
   * Disconnect from the database
   */
  $disconnect(): $Utils.JsPromise<void>;

  /**
   * Add a middleware
   * @deprecated since 4.16.0. For new code, prefer client extensions instead.
   * @see https://pris.ly/d/extensions
   */
  $use(cb: Prisma.Middleware): void

/**
   * Executes a prepared raw query and returns the number of affected rows.
   * @example
   * ```
   * const result = await prisma.$executeRaw`UPDATE User SET cool = ${true} WHERE email = ${'user@email.com'};`
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Executes a raw query and returns the number of affected rows.
   * Susceptible to SQL injections, see documentation.
   * @example
   * ```
   * const result = await prisma.$executeRawUnsafe('UPDATE User SET cool = $1 WHERE email = $2 ;', true, 'user@email.com')
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Performs a prepared raw query and returns the `SELECT` data.
   * @example
   * ```
   * const result = await prisma.$queryRaw`SELECT * FROM User WHERE id = ${1} OR email = ${'user@email.com'};`
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<T>;

  /**
   * Performs a raw query and returns the `SELECT` data.
   * Susceptible to SQL injections, see documentation.
   * @example
   * ```
   * const result = await prisma.$queryRawUnsafe('SELECT * FROM User WHERE id = $1 OR email = $2;', 1, 'user@email.com')
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<T>;


  /**
   * Allows the running of a sequence of read/write operations that are guaranteed to either succeed or fail as a whole.
   * @example
   * ```
   * const [george, bob, alice] = await prisma.$transaction([
   *   prisma.user.create({ data: { name: 'George' } }),
   *   prisma.user.create({ data: { name: 'Bob' } }),
   *   prisma.user.create({ data: { name: 'Alice' } }),
   * ])
   * ```
   * 
   * Read more in our [docs](https://www.prisma.io/docs/concepts/components/prisma-client/transactions).
   */
  $transaction<P extends Prisma.PrismaPromise<any>[]>(arg: [...P], options?: { isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<runtime.Types.Utils.UnwrapTuple<P>>

  $transaction<R>(fn: (prisma: Omit<PrismaClient, runtime.ITXClientDenyList>) => $Utils.JsPromise<R>, options?: { maxWait?: number, timeout?: number, isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<R>


  $extends: $Extensions.ExtendsHook<"extends", Prisma.TypeMapCb<ClientOptions>, ExtArgs, $Utils.Call<Prisma.TypeMapCb<ClientOptions>, {
    extArgs: ExtArgs
  }>>

      /**
   * `prisma.user`: Exposes CRUD operations for the **User** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Users
    * const users = await prisma.user.findMany()
    * ```
    */
  get user(): Prisma.UserDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.mandiLatLong`: Exposes CRUD operations for the **MandiLatLong** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more MandiLatLongs
    * const mandiLatLongs = await prisma.mandiLatLong.findMany()
    * ```
    */
  get mandiLatLong(): Prisma.MandiLatLongDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.truck`: Exposes CRUD operations for the **Truck** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Trucks
    * const trucks = await prisma.truck.findMany()
    * ```
    */
  get truck(): Prisma.TruckDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.voiceResponse`: Exposes CRUD operations for the **VoiceResponse** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more VoiceResponses
    * const voiceResponses = await prisma.voiceResponse.findMany()
    * ```
    */
  get voiceResponse(): Prisma.VoiceResponseDelegate<ExtArgs, ClientOptions>;
}

export namespace Prisma {
  export import DMMF = runtime.DMMF

  export type PrismaPromise<T> = $Public.PrismaPromise<T>

  /**
   * Validator
   */
  export import validator = runtime.Public.validator

  /**
   * Prisma Errors
   */
  export import PrismaClientKnownRequestError = runtime.PrismaClientKnownRequestError
  export import PrismaClientUnknownRequestError = runtime.PrismaClientUnknownRequestError
  export import PrismaClientRustPanicError = runtime.PrismaClientRustPanicError
  export import PrismaClientInitializationError = runtime.PrismaClientInitializationError
  export import PrismaClientValidationError = runtime.PrismaClientValidationError

  /**
   * Re-export of sql-template-tag
   */
  export import sql = runtime.sqltag
  export import empty = runtime.empty
  export import join = runtime.join
  export import raw = runtime.raw
  export import Sql = runtime.Sql



  /**
   * Decimal.js
   */
  export import Decimal = runtime.Decimal

  export type DecimalJsLike = runtime.DecimalJsLike

  /**
   * Metrics
   */
  export type Metrics = runtime.Metrics
  export type Metric<T> = runtime.Metric<T>
  export type MetricHistogram = runtime.MetricHistogram
  export type MetricHistogramBucket = runtime.MetricHistogramBucket

  /**
  * Extensions
  */
  export import Extension = $Extensions.UserArgs
  export import getExtensionContext = runtime.Extensions.getExtensionContext
  export import Args = $Public.Args
  export import Payload = $Public.Payload
  export import Result = $Public.Result
  export import Exact = $Public.Exact

  /**
   * Prisma Client JS version: 6.8.1
   * Query Engine version: 2060c79ba17c6bb9f5823312b6f6b7f4a845738e
   */
  export type PrismaVersion = {
    client: string
  }

  export const prismaVersion: PrismaVersion

  /**
   * Utility Types
   */


  export import JsonObject = runtime.JsonObject
  export import JsonArray = runtime.JsonArray
  export import JsonValue = runtime.JsonValue
  export import InputJsonObject = runtime.InputJsonObject
  export import InputJsonArray = runtime.InputJsonArray
  export import InputJsonValue = runtime.InputJsonValue

  /**
   * Types of the values used to represent different kinds of `null` values when working with JSON fields.
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  namespace NullTypes {
    /**
    * Type of `Prisma.DbNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.DbNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class DbNull {
      private DbNull: never
      private constructor()
    }

    /**
    * Type of `Prisma.JsonNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.JsonNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class JsonNull {
      private JsonNull: never
      private constructor()
    }

    /**
    * Type of `Prisma.AnyNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.AnyNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class AnyNull {
      private AnyNull: never
      private constructor()
    }
  }

  /**
   * Helper for filtering JSON entries that have `null` on the database (empty on the db)
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const DbNull: NullTypes.DbNull

  /**
   * Helper for filtering JSON entries that have JSON `null` values (not empty on the db)
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const JsonNull: NullTypes.JsonNull

  /**
   * Helper for filtering JSON entries that are `Prisma.DbNull` or `Prisma.JsonNull`
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const AnyNull: NullTypes.AnyNull

  type SelectAndInclude = {
    select: any
    include: any
  }

  type SelectAndOmit = {
    select: any
    omit: any
  }

  /**
   * Get the type of the value, that the Promise holds.
   */
  export type PromiseType<T extends PromiseLike<any>> = T extends PromiseLike<infer U> ? U : T;

  /**
   * Get the return type of a function which returns a Promise.
   */
  export type PromiseReturnType<T extends (...args: any) => $Utils.JsPromise<any>> = PromiseType<ReturnType<T>>

  /**
   * From T, pick a set of properties whose keys are in the union K
   */
  type Prisma__Pick<T, K extends keyof T> = {
      [P in K]: T[P];
  };


  export type Enumerable<T> = T | Array<T>;

  export type RequiredKeys<T> = {
    [K in keyof T]-?: {} extends Prisma__Pick<T, K> ? never : K
  }[keyof T]

  export type TruthyKeys<T> = keyof {
    [K in keyof T as T[K] extends false | undefined | null ? never : K]: K
  }

  export type TrueKeys<T> = TruthyKeys<Prisma__Pick<T, RequiredKeys<T>>>

  /**
   * Subset
   * @desc From `T` pick properties that exist in `U`. Simple version of Intersection
   */
  export type Subset<T, U> = {
    [key in keyof T]: key extends keyof U ? T[key] : never;
  };

  /**
   * SelectSubset
   * @desc From `T` pick properties that exist in `U`. Simple version of Intersection.
   * Additionally, it validates, if both select and include are present. If the case, it errors.
   */
  export type SelectSubset<T, U> = {
    [key in keyof T]: key extends keyof U ? T[key] : never
  } &
    (T extends SelectAndInclude
      ? 'Please either choose `select` or `include`.'
      : T extends SelectAndOmit
        ? 'Please either choose `select` or `omit`.'
        : {})

  /**
   * Subset + Intersection
   * @desc From `T` pick properties that exist in `U` and intersect `K`
   */
  export type SubsetIntersection<T, U, K> = {
    [key in keyof T]: key extends keyof U ? T[key] : never
  } &
    K

  type Without<T, U> = { [P in Exclude<keyof T, keyof U>]?: never };

  /**
   * XOR is needed to have a real mutually exclusive union type
   * https://stackoverflow.com/questions/42123407/does-typescript-support-mutually-exclusive-types
   */
  type XOR<T, U> =
    T extends object ?
    U extends object ?
      (Without<T, U> & U) | (Without<U, T> & T)
    : U : T


  /**
   * Is T a Record?
   */
  type IsObject<T extends any> = T extends Array<any>
  ? False
  : T extends Date
  ? False
  : T extends Uint8Array
  ? False
  : T extends BigInt
  ? False
  : T extends object
  ? True
  : False


  /**
   * If it's T[], return T
   */
  export type UnEnumerate<T extends unknown> = T extends Array<infer U> ? U : T

  /**
   * From ts-toolbelt
   */

  type __Either<O extends object, K extends Key> = Omit<O, K> &
    {
      // Merge all but K
      [P in K]: Prisma__Pick<O, P & keyof O> // With K possibilities
    }[K]

  type EitherStrict<O extends object, K extends Key> = Strict<__Either<O, K>>

  type EitherLoose<O extends object, K extends Key> = ComputeRaw<__Either<O, K>>

  type _Either<
    O extends object,
    K extends Key,
    strict extends Boolean
  > = {
    1: EitherStrict<O, K>
    0: EitherLoose<O, K>
  }[strict]

  type Either<
    O extends object,
    K extends Key,
    strict extends Boolean = 1
  > = O extends unknown ? _Either<O, K, strict> : never

  export type Union = any

  type PatchUndefined<O extends object, O1 extends object> = {
    [K in keyof O]: O[K] extends undefined ? At<O1, K> : O[K]
  } & {}

  /** Helper Types for "Merge" **/
  export type IntersectOf<U extends Union> = (
    U extends unknown ? (k: U) => void : never
  ) extends (k: infer I) => void
    ? I
    : never

  export type Overwrite<O extends object, O1 extends object> = {
      [K in keyof O]: K extends keyof O1 ? O1[K] : O[K];
  } & {};

  type _Merge<U extends object> = IntersectOf<Overwrite<U, {
      [K in keyof U]-?: At<U, K>;
  }>>;

  type Key = string | number | symbol;
  type AtBasic<O extends object, K extends Key> = K extends keyof O ? O[K] : never;
  type AtStrict<O extends object, K extends Key> = O[K & keyof O];
  type AtLoose<O extends object, K extends Key> = O extends unknown ? AtStrict<O, K> : never;
  export type At<O extends object, K extends Key, strict extends Boolean = 1> = {
      1: AtStrict<O, K>;
      0: AtLoose<O, K>;
  }[strict];

  export type ComputeRaw<A extends any> = A extends Function ? A : {
    [K in keyof A]: A[K];
  } & {};

  export type OptionalFlat<O> = {
    [K in keyof O]?: O[K];
  } & {};

  type _Record<K extends keyof any, T> = {
    [P in K]: T;
  };

  // cause typescript not to expand types and preserve names
  type NoExpand<T> = T extends unknown ? T : never;

  // this type assumes the passed object is entirely optional
  type AtLeast<O extends object, K extends string> = NoExpand<
    O extends unknown
    ? | (K extends keyof O ? { [P in K]: O[P] } & O : O)
      | {[P in keyof O as P extends K ? P : never]-?: O[P]} & O
    : never>;

  type _Strict<U, _U = U> = U extends unknown ? U & OptionalFlat<_Record<Exclude<Keys<_U>, keyof U>, never>> : never;

  export type Strict<U extends object> = ComputeRaw<_Strict<U>>;
  /** End Helper Types for "Merge" **/

  export type Merge<U extends object> = ComputeRaw<_Merge<Strict<U>>>;

  /**
  A [[Boolean]]
  */
  export type Boolean = True | False

  // /**
  // 1
  // */
  export type True = 1

  /**
  0
  */
  export type False = 0

  export type Not<B extends Boolean> = {
    0: 1
    1: 0
  }[B]

  export type Extends<A1 extends any, A2 extends any> = [A1] extends [never]
    ? 0 // anything `never` is false
    : A1 extends A2
    ? 1
    : 0

  export type Has<U extends Union, U1 extends Union> = Not<
    Extends<Exclude<U1, U>, U1>
  >

  export type Or<B1 extends Boolean, B2 extends Boolean> = {
    0: {
      0: 0
      1: 1
    }
    1: {
      0: 1
      1: 1
    }
  }[B1][B2]

  export type Keys<U extends Union> = U extends unknown ? keyof U : never

  type Cast<A, B> = A extends B ? A : B;

  export const type: unique symbol;



  /**
   * Used by group by
   */

  export type GetScalarType<T, O> = O extends object ? {
    [P in keyof T]: P extends keyof O
      ? O[P]
      : never
  } : never

  type FieldPaths<
    T,
    U = Omit<T, '_avg' | '_sum' | '_count' | '_min' | '_max'>
  > = IsObject<T> extends True ? U : T

  type GetHavingFields<T> = {
    [K in keyof T]: Or<
      Or<Extends<'OR', K>, Extends<'AND', K>>,
      Extends<'NOT', K>
    > extends True
      ? // infer is only needed to not hit TS limit
        // based on the brilliant idea of Pierre-Antoine Mills
        // https://github.com/microsoft/TypeScript/issues/30188#issuecomment-478938437
        T[K] extends infer TK
        ? GetHavingFields<UnEnumerate<TK> extends object ? Merge<UnEnumerate<TK>> : never>
        : never
      : {} extends FieldPaths<T[K]>
      ? never
      : K
  }[keyof T]

  /**
   * Convert tuple to union
   */
  type _TupleToUnion<T> = T extends (infer E)[] ? E : never
  type TupleToUnion<K extends readonly any[]> = _TupleToUnion<K>
  type MaybeTupleToUnion<T> = T extends any[] ? TupleToUnion<T> : T

  /**
   * Like `Pick`, but additionally can also accept an array of keys
   */
  type PickEnumerable<T, K extends Enumerable<keyof T> | keyof T> = Prisma__Pick<T, MaybeTupleToUnion<K>>

  /**
   * Exclude all keys with underscores
   */
  type ExcludeUnderscoreKeys<T extends string> = T extends `_${string}` ? never : T


  export type FieldRef<Model, FieldType> = runtime.FieldRef<Model, FieldType>

  type FieldRefInputType<Model, FieldType> = Model extends never ? never : FieldRef<Model, FieldType>


  export const ModelName: {
    User: 'User',
    MandiLatLong: 'MandiLatLong',
    Truck: 'Truck',
    VoiceResponse: 'VoiceResponse'
  };

  export type ModelName = (typeof ModelName)[keyof typeof ModelName]


  export type Datasources = {
    db?: Datasource
  }

  interface TypeMapCb<ClientOptions = {}> extends $Utils.Fn<{extArgs: $Extensions.InternalArgs }, $Utils.Record<string, any>> {
    returns: Prisma.TypeMap<this['params']['extArgs'], ClientOptions extends { omit: infer OmitOptions } ? OmitOptions : {}>
  }

  export type TypeMap<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> = {
    globalOmitOptions: {
      omit: GlobalOmitOptions
    }
    meta: {
      modelProps: "user" | "mandiLatLong" | "truck" | "voiceResponse"
      txIsolationLevel: Prisma.TransactionIsolationLevel
    }
    model: {
      User: {
        payload: Prisma.$UserPayload<ExtArgs>
        fields: Prisma.UserFieldRefs
        operations: {
          findUnique: {
            args: Prisma.UserFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.UserFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          findFirst: {
            args: Prisma.UserFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.UserFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          findMany: {
            args: Prisma.UserFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          create: {
            args: Prisma.UserCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          createMany: {
            args: Prisma.UserCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.UserCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          delete: {
            args: Prisma.UserDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          update: {
            args: Prisma.UserUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          deleteMany: {
            args: Prisma.UserDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.UserUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.UserUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          upsert: {
            args: Prisma.UserUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          aggregate: {
            args: Prisma.UserAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateUser>
          }
          groupBy: {
            args: Prisma.UserGroupByArgs<ExtArgs>
            result: $Utils.Optional<UserGroupByOutputType>[]
          }
          count: {
            args: Prisma.UserCountArgs<ExtArgs>
            result: $Utils.Optional<UserCountAggregateOutputType> | number
          }
        }
      }
      MandiLatLong: {
        payload: Prisma.$MandiLatLongPayload<ExtArgs>
        fields: Prisma.MandiLatLongFieldRefs
        operations: {
          findUnique: {
            args: Prisma.MandiLatLongFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.MandiLatLongFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>
          }
          findFirst: {
            args: Prisma.MandiLatLongFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.MandiLatLongFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>
          }
          findMany: {
            args: Prisma.MandiLatLongFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>[]
          }
          create: {
            args: Prisma.MandiLatLongCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>
          }
          createMany: {
            args: Prisma.MandiLatLongCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.MandiLatLongCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>[]
          }
          delete: {
            args: Prisma.MandiLatLongDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>
          }
          update: {
            args: Prisma.MandiLatLongUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>
          }
          deleteMany: {
            args: Prisma.MandiLatLongDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.MandiLatLongUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.MandiLatLongUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>[]
          }
          upsert: {
            args: Prisma.MandiLatLongUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$MandiLatLongPayload>
          }
          aggregate: {
            args: Prisma.MandiLatLongAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateMandiLatLong>
          }
          groupBy: {
            args: Prisma.MandiLatLongGroupByArgs<ExtArgs>
            result: $Utils.Optional<MandiLatLongGroupByOutputType>[]
          }
          count: {
            args: Prisma.MandiLatLongCountArgs<ExtArgs>
            result: $Utils.Optional<MandiLatLongCountAggregateOutputType> | number
          }
        }
      }
      Truck: {
        payload: Prisma.$TruckPayload<ExtArgs>
        fields: Prisma.TruckFieldRefs
        operations: {
          findUnique: {
            args: Prisma.TruckFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.TruckFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>
          }
          findFirst: {
            args: Prisma.TruckFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.TruckFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>
          }
          findMany: {
            args: Prisma.TruckFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>[]
          }
          create: {
            args: Prisma.TruckCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>
          }
          createMany: {
            args: Prisma.TruckCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.TruckCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>[]
          }
          delete: {
            args: Prisma.TruckDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>
          }
          update: {
            args: Prisma.TruckUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>
          }
          deleteMany: {
            args: Prisma.TruckDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.TruckUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.TruckUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>[]
          }
          upsert: {
            args: Prisma.TruckUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$TruckPayload>
          }
          aggregate: {
            args: Prisma.TruckAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateTruck>
          }
          groupBy: {
            args: Prisma.TruckGroupByArgs<ExtArgs>
            result: $Utils.Optional<TruckGroupByOutputType>[]
          }
          count: {
            args: Prisma.TruckCountArgs<ExtArgs>
            result: $Utils.Optional<TruckCountAggregateOutputType> | number
          }
        }
      }
      VoiceResponse: {
        payload: Prisma.$VoiceResponsePayload<ExtArgs>
        fields: Prisma.VoiceResponseFieldRefs
        operations: {
          findUnique: {
            args: Prisma.VoiceResponseFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.VoiceResponseFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>
          }
          findFirst: {
            args: Prisma.VoiceResponseFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.VoiceResponseFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>
          }
          findMany: {
            args: Prisma.VoiceResponseFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>[]
          }
          create: {
            args: Prisma.VoiceResponseCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>
          }
          createMany: {
            args: Prisma.VoiceResponseCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.VoiceResponseCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>[]
          }
          delete: {
            args: Prisma.VoiceResponseDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>
          }
          update: {
            args: Prisma.VoiceResponseUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>
          }
          deleteMany: {
            args: Prisma.VoiceResponseDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.VoiceResponseUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.VoiceResponseUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>[]
          }
          upsert: {
            args: Prisma.VoiceResponseUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VoiceResponsePayload>
          }
          aggregate: {
            args: Prisma.VoiceResponseAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateVoiceResponse>
          }
          groupBy: {
            args: Prisma.VoiceResponseGroupByArgs<ExtArgs>
            result: $Utils.Optional<VoiceResponseGroupByOutputType>[]
          }
          count: {
            args: Prisma.VoiceResponseCountArgs<ExtArgs>
            result: $Utils.Optional<VoiceResponseCountAggregateOutputType> | number
          }
        }
      }
    }
  } & {
    other: {
      payload: any
      operations: {
        $executeRaw: {
          args: [query: TemplateStringsArray | Prisma.Sql, ...values: any[]],
          result: any
        }
        $executeRawUnsafe: {
          args: [query: string, ...values: any[]],
          result: any
        }
        $queryRaw: {
          args: [query: TemplateStringsArray | Prisma.Sql, ...values: any[]],
          result: any
        }
        $queryRawUnsafe: {
          args: [query: string, ...values: any[]],
          result: any
        }
      }
    }
  }
  export const defineExtension: $Extensions.ExtendsHook<"define", Prisma.TypeMapCb, $Extensions.DefaultArgs>
  export type DefaultPrismaClient = PrismaClient
  export type ErrorFormat = 'pretty' | 'colorless' | 'minimal'
  export interface PrismaClientOptions {
    /**
     * Overwrites the datasource url from your schema.prisma file
     */
    datasources?: Datasources
    /**
     * Overwrites the datasource url from your schema.prisma file
     */
    datasourceUrl?: string
    /**
     * @default "colorless"
     */
    errorFormat?: ErrorFormat
    /**
     * @example
     * ```
     * // Defaults to stdout
     * log: ['query', 'info', 'warn', 'error']
     * 
     * // Emit as events
     * log: [
     *   { emit: 'stdout', level: 'query' },
     *   { emit: 'stdout', level: 'info' },
     *   { emit: 'stdout', level: 'warn' }
     *   { emit: 'stdout', level: 'error' }
     * ]
     * ```
     * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/logging#the-log-option).
     */
    log?: (LogLevel | LogDefinition)[]
    /**
     * The default values for transactionOptions
     * maxWait ?= 2000
     * timeout ?= 5000
     */
    transactionOptions?: {
      maxWait?: number
      timeout?: number
      isolationLevel?: Prisma.TransactionIsolationLevel
    }
    /**
     * Global configuration for omitting model fields by default.
     * 
     * @example
     * ```
     * const prisma = new PrismaClient({
     *   omit: {
     *     user: {
     *       password: true
     *     }
     *   }
     * })
     * ```
     */
    omit?: Prisma.GlobalOmitConfig
  }
  export type GlobalOmitConfig = {
    user?: UserOmit
    mandiLatLong?: MandiLatLongOmit
    truck?: TruckOmit
    voiceResponse?: VoiceResponseOmit
  }

  /* Types for Logging */
  export type LogLevel = 'info' | 'query' | 'warn' | 'error'
  export type LogDefinition = {
    level: LogLevel
    emit: 'stdout' | 'event'
  }

  export type GetLogType<T extends LogLevel | LogDefinition> = T extends LogDefinition ? T['emit'] extends 'event' ? T['level'] : never : never
  export type GetEvents<T extends any> = T extends Array<LogLevel | LogDefinition> ?
    GetLogType<T[0]> | GetLogType<T[1]> | GetLogType<T[2]> | GetLogType<T[3]>
    : never

  export type QueryEvent = {
    timestamp: Date
    query: string
    params: string
    duration: number
    target: string
  }

  export type LogEvent = {
    timestamp: Date
    message: string
    target: string
  }
  /* End Types for Logging */


  export type PrismaAction =
    | 'findUnique'
    | 'findUniqueOrThrow'
    | 'findMany'
    | 'findFirst'
    | 'findFirstOrThrow'
    | 'create'
    | 'createMany'
    | 'createManyAndReturn'
    | 'update'
    | 'updateMany'
    | 'updateManyAndReturn'
    | 'upsert'
    | 'delete'
    | 'deleteMany'
    | 'executeRaw'
    | 'queryRaw'
    | 'aggregate'
    | 'count'
    | 'runCommandRaw'
    | 'findRaw'
    | 'groupBy'

  /**
   * These options are being passed into the middleware as "params"
   */
  export type MiddlewareParams = {
    model?: ModelName
    action: PrismaAction
    args: any
    dataPath: string[]
    runInTransaction: boolean
  }

  /**
   * The `T` type makes sure, that the `return proceed` is not forgotten in the middleware implementation
   */
  export type Middleware<T = any> = (
    params: MiddlewareParams,
    next: (params: MiddlewareParams) => $Utils.JsPromise<T>,
  ) => $Utils.JsPromise<T>

  // tested in getLogLevel.test.ts
  export function getLogLevel(log: Array<LogLevel | LogDefinition>): LogLevel | undefined;

  /**
   * `PrismaClient` proxy available in interactive transactions.
   */
  export type TransactionClient = Omit<Prisma.DefaultPrismaClient, runtime.ITXClientDenyList>

  export type Datasource = {
    url?: string
  }

  /**
   * Count Types
   */



  /**
   * Models
   */

  /**
   * Model User
   */

  export type AggregateUser = {
    _count: UserCountAggregateOutputType | null
    _min: UserMinAggregateOutputType | null
    _max: UserMaxAggregateOutputType | null
  }

  export type UserMinAggregateOutputType = {
    id: string | null
    email: string | null
    firstName: string | null
    lastName: string | null
    profileImage: string | null
    createdAt: Date | null
  }

  export type UserMaxAggregateOutputType = {
    id: string | null
    email: string | null
    firstName: string | null
    lastName: string | null
    profileImage: string | null
    createdAt: Date | null
  }

  export type UserCountAggregateOutputType = {
    id: number
    email: number
    firstName: number
    lastName: number
    profileImage: number
    createdAt: number
    _all: number
  }


  export type UserMinAggregateInputType = {
    id?: true
    email?: true
    firstName?: true
    lastName?: true
    profileImage?: true
    createdAt?: true
  }

  export type UserMaxAggregateInputType = {
    id?: true
    email?: true
    firstName?: true
    lastName?: true
    profileImage?: true
    createdAt?: true
  }

  export type UserCountAggregateInputType = {
    id?: true
    email?: true
    firstName?: true
    lastName?: true
    profileImage?: true
    createdAt?: true
    _all?: true
  }

  export type UserAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which User to aggregate.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Users
    **/
    _count?: true | UserCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: UserMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: UserMaxAggregateInputType
  }

  export type GetUserAggregateType<T extends UserAggregateArgs> = {
        [P in keyof T & keyof AggregateUser]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateUser[P]>
      : GetScalarType<T[P], AggregateUser[P]>
  }




  export type UserGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: UserWhereInput
    orderBy?: UserOrderByWithAggregationInput | UserOrderByWithAggregationInput[]
    by: UserScalarFieldEnum[] | UserScalarFieldEnum
    having?: UserScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: UserCountAggregateInputType | true
    _min?: UserMinAggregateInputType
    _max?: UserMaxAggregateInputType
  }

  export type UserGroupByOutputType = {
    id: string
    email: string
    firstName: string
    lastName: string
    profileImage: string
    createdAt: Date
    _count: UserCountAggregateOutputType | null
    _min: UserMinAggregateOutputType | null
    _max: UserMaxAggregateOutputType | null
  }

  type GetUserGroupByPayload<T extends UserGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<UserGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof UserGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], UserGroupByOutputType[P]>
            : GetScalarType<T[P], UserGroupByOutputType[P]>
        }
      >
    >


  export type UserSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    email?: boolean
    firstName?: boolean
    lastName?: boolean
    profileImage?: boolean
    createdAt?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    email?: boolean
    firstName?: boolean
    lastName?: boolean
    profileImage?: boolean
    createdAt?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    email?: boolean
    firstName?: boolean
    lastName?: boolean
    profileImage?: boolean
    createdAt?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectScalar = {
    id?: boolean
    email?: boolean
    firstName?: boolean
    lastName?: boolean
    profileImage?: boolean
    createdAt?: boolean
  }

  export type UserOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "email" | "firstName" | "lastName" | "profileImage" | "createdAt", ExtArgs["result"]["user"]>

  export type $UserPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "User"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      id: string
      email: string
      firstName: string
      lastName: string
      profileImage: string
      createdAt: Date
    }, ExtArgs["result"]["user"]>
    composites: {}
  }

  type UserGetPayload<S extends boolean | null | undefined | UserDefaultArgs> = $Result.GetResult<Prisma.$UserPayload, S>

  type UserCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<UserFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: UserCountAggregateInputType | true
    }

  export interface UserDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['User'], meta: { name: 'User' } }
    /**
     * Find zero or one User that matches the filter.
     * @param {UserFindUniqueArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends UserFindUniqueArgs>(args: SelectSubset<T, UserFindUniqueArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one User that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {UserFindUniqueOrThrowArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends UserFindUniqueOrThrowArgs>(args: SelectSubset<T, UserFindUniqueOrThrowArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first User that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindFirstArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends UserFindFirstArgs>(args?: SelectSubset<T, UserFindFirstArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first User that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindFirstOrThrowArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends UserFindFirstOrThrowArgs>(args?: SelectSubset<T, UserFindFirstOrThrowArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Users that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Users
     * const users = await prisma.user.findMany()
     * 
     * // Get first 10 Users
     * const users = await prisma.user.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const userWithIdOnly = await prisma.user.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends UserFindManyArgs>(args?: SelectSubset<T, UserFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a User.
     * @param {UserCreateArgs} args - Arguments to create a User.
     * @example
     * // Create one User
     * const User = await prisma.user.create({
     *   data: {
     *     // ... data to create a User
     *   }
     * })
     * 
     */
    create<T extends UserCreateArgs>(args: SelectSubset<T, UserCreateArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Users.
     * @param {UserCreateManyArgs} args - Arguments to create many Users.
     * @example
     * // Create many Users
     * const user = await prisma.user.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends UserCreateManyArgs>(args?: SelectSubset<T, UserCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Users and returns the data saved in the database.
     * @param {UserCreateManyAndReturnArgs} args - Arguments to create many Users.
     * @example
     * // Create many Users
     * const user = await prisma.user.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Users and only return the `id`
     * const userWithIdOnly = await prisma.user.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends UserCreateManyAndReturnArgs>(args?: SelectSubset<T, UserCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a User.
     * @param {UserDeleteArgs} args - Arguments to delete one User.
     * @example
     * // Delete one User
     * const User = await prisma.user.delete({
     *   where: {
     *     // ... filter to delete one User
     *   }
     * })
     * 
     */
    delete<T extends UserDeleteArgs>(args: SelectSubset<T, UserDeleteArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one User.
     * @param {UserUpdateArgs} args - Arguments to update one User.
     * @example
     * // Update one User
     * const user = await prisma.user.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends UserUpdateArgs>(args: SelectSubset<T, UserUpdateArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Users.
     * @param {UserDeleteManyArgs} args - Arguments to filter Users to delete.
     * @example
     * // Delete a few Users
     * const { count } = await prisma.user.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends UserDeleteManyArgs>(args?: SelectSubset<T, UserDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Users.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Users
     * const user = await prisma.user.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends UserUpdateManyArgs>(args: SelectSubset<T, UserUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Users and returns the data updated in the database.
     * @param {UserUpdateManyAndReturnArgs} args - Arguments to update many Users.
     * @example
     * // Update many Users
     * const user = await prisma.user.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Users and only return the `id`
     * const userWithIdOnly = await prisma.user.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends UserUpdateManyAndReturnArgs>(args: SelectSubset<T, UserUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one User.
     * @param {UserUpsertArgs} args - Arguments to update or create a User.
     * @example
     * // Update or create a User
     * const user = await prisma.user.upsert({
     *   create: {
     *     // ... data to create a User
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the User we want to update
     *   }
     * })
     */
    upsert<T extends UserUpsertArgs>(args: SelectSubset<T, UserUpsertArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Users.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserCountArgs} args - Arguments to filter Users to count.
     * @example
     * // Count the number of Users
     * const count = await prisma.user.count({
     *   where: {
     *     // ... the filter for the Users we want to count
     *   }
     * })
    **/
    count<T extends UserCountArgs>(
      args?: Subset<T, UserCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], UserCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a User.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends UserAggregateArgs>(args: Subset<T, UserAggregateArgs>): Prisma.PrismaPromise<GetUserAggregateType<T>>

    /**
     * Group by User.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends UserGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: UserGroupByArgs['orderBy'] }
        : { orderBy?: UserGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, UserGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetUserGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the User model
   */
  readonly fields: UserFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for User.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__UserClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the User model
   */
  interface UserFieldRefs {
    readonly id: FieldRef<"User", 'String'>
    readonly email: FieldRef<"User", 'String'>
    readonly firstName: FieldRef<"User", 'String'>
    readonly lastName: FieldRef<"User", 'String'>
    readonly profileImage: FieldRef<"User", 'String'>
    readonly createdAt: FieldRef<"User", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * User findUnique
   */
  export type UserFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User findUniqueOrThrow
   */
  export type UserFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User findFirst
   */
  export type UserFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Users.
     */
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User findFirstOrThrow
   */
  export type UserFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Users.
     */
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User findMany
   */
  export type UserFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Filter, which Users to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User create
   */
  export type UserCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data needed to create a User.
     */
    data: XOR<UserCreateInput, UserUncheckedCreateInput>
  }

  /**
   * User createMany
   */
  export type UserCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Users.
     */
    data: UserCreateManyInput | UserCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * User createManyAndReturn
   */
  export type UserCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data used to create many Users.
     */
    data: UserCreateManyInput | UserCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * User update
   */
  export type UserUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data needed to update a User.
     */
    data: XOR<UserUpdateInput, UserUncheckedUpdateInput>
    /**
     * Choose, which User to update.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User updateMany
   */
  export type UserUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Users.
     */
    data: XOR<UserUpdateManyMutationInput, UserUncheckedUpdateManyInput>
    /**
     * Filter which Users to update
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to update.
     */
    limit?: number
  }

  /**
   * User updateManyAndReturn
   */
  export type UserUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data used to update Users.
     */
    data: XOR<UserUpdateManyMutationInput, UserUncheckedUpdateManyInput>
    /**
     * Filter which Users to update
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to update.
     */
    limit?: number
  }

  /**
   * User upsert
   */
  export type UserUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The filter to search for the User to update in case it exists.
     */
    where: UserWhereUniqueInput
    /**
     * In case the User found by the `where` argument doesn't exist, create a new User with this data.
     */
    create: XOR<UserCreateInput, UserUncheckedCreateInput>
    /**
     * In case the User was found with the provided `where` argument, update it with this data.
     */
    update: XOR<UserUpdateInput, UserUncheckedUpdateInput>
  }

  /**
   * User delete
   */
  export type UserDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Filter which User to delete.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User deleteMany
   */
  export type UserDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Users to delete
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to delete.
     */
    limit?: number
  }

  /**
   * User without action
   */
  export type UserDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
  }


  /**
   * Model MandiLatLong
   */

  export type AggregateMandiLatLong = {
    _count: MandiLatLongCountAggregateOutputType | null
    _avg: MandiLatLongAvgAggregateOutputType | null
    _sum: MandiLatLongSumAggregateOutputType | null
    _min: MandiLatLongMinAggregateOutputType | null
    _max: MandiLatLongMaxAggregateOutputType | null
  }

  export type MandiLatLongAvgAggregateOutputType = {
    id: number | null
    Latitude: number | null
    Longitude: number | null
  }

  export type MandiLatLongSumAggregateOutputType = {
    id: number | null
    Latitude: number | null
    Longitude: number | null
  }

  export type MandiLatLongMinAggregateOutputType = {
    id: number | null
    State: string | null
    Mandi: string | null
    Mandi_Hindi: string | null
    Latitude: number | null
    Longitude: number | null
  }

  export type MandiLatLongMaxAggregateOutputType = {
    id: number | null
    State: string | null
    Mandi: string | null
    Mandi_Hindi: string | null
    Latitude: number | null
    Longitude: number | null
  }

  export type MandiLatLongCountAggregateOutputType = {
    id: number
    State: number
    Mandi: number
    Mandi_Hindi: number
    Latitude: number
    Longitude: number
    _all: number
  }


  export type MandiLatLongAvgAggregateInputType = {
    id?: true
    Latitude?: true
    Longitude?: true
  }

  export type MandiLatLongSumAggregateInputType = {
    id?: true
    Latitude?: true
    Longitude?: true
  }

  export type MandiLatLongMinAggregateInputType = {
    id?: true
    State?: true
    Mandi?: true
    Mandi_Hindi?: true
    Latitude?: true
    Longitude?: true
  }

  export type MandiLatLongMaxAggregateInputType = {
    id?: true
    State?: true
    Mandi?: true
    Mandi_Hindi?: true
    Latitude?: true
    Longitude?: true
  }

  export type MandiLatLongCountAggregateInputType = {
    id?: true
    State?: true
    Mandi?: true
    Mandi_Hindi?: true
    Latitude?: true
    Longitude?: true
    _all?: true
  }

  export type MandiLatLongAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which MandiLatLong to aggregate.
     */
    where?: MandiLatLongWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of MandiLatLongs to fetch.
     */
    orderBy?: MandiLatLongOrderByWithRelationInput | MandiLatLongOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: MandiLatLongWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` MandiLatLongs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` MandiLatLongs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned MandiLatLongs
    **/
    _count?: true | MandiLatLongCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: MandiLatLongAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: MandiLatLongSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: MandiLatLongMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: MandiLatLongMaxAggregateInputType
  }

  export type GetMandiLatLongAggregateType<T extends MandiLatLongAggregateArgs> = {
        [P in keyof T & keyof AggregateMandiLatLong]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateMandiLatLong[P]>
      : GetScalarType<T[P], AggregateMandiLatLong[P]>
  }




  export type MandiLatLongGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: MandiLatLongWhereInput
    orderBy?: MandiLatLongOrderByWithAggregationInput | MandiLatLongOrderByWithAggregationInput[]
    by: MandiLatLongScalarFieldEnum[] | MandiLatLongScalarFieldEnum
    having?: MandiLatLongScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: MandiLatLongCountAggregateInputType | true
    _avg?: MandiLatLongAvgAggregateInputType
    _sum?: MandiLatLongSumAggregateInputType
    _min?: MandiLatLongMinAggregateInputType
    _max?: MandiLatLongMaxAggregateInputType
  }

  export type MandiLatLongGroupByOutputType = {
    id: number
    State: string
    Mandi: string
    Mandi_Hindi: string
    Latitude: number | null
    Longitude: number | null
    _count: MandiLatLongCountAggregateOutputType | null
    _avg: MandiLatLongAvgAggregateOutputType | null
    _sum: MandiLatLongSumAggregateOutputType | null
    _min: MandiLatLongMinAggregateOutputType | null
    _max: MandiLatLongMaxAggregateOutputType | null
  }

  type GetMandiLatLongGroupByPayload<T extends MandiLatLongGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<MandiLatLongGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof MandiLatLongGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], MandiLatLongGroupByOutputType[P]>
            : GetScalarType<T[P], MandiLatLongGroupByOutputType[P]>
        }
      >
    >


  export type MandiLatLongSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    State?: boolean
    Mandi?: boolean
    Mandi_Hindi?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }, ExtArgs["result"]["mandiLatLong"]>

  export type MandiLatLongSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    State?: boolean
    Mandi?: boolean
    Mandi_Hindi?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }, ExtArgs["result"]["mandiLatLong"]>

  export type MandiLatLongSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    State?: boolean
    Mandi?: boolean
    Mandi_Hindi?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }, ExtArgs["result"]["mandiLatLong"]>

  export type MandiLatLongSelectScalar = {
    id?: boolean
    State?: boolean
    Mandi?: boolean
    Mandi_Hindi?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }

  export type MandiLatLongOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "State" | "Mandi" | "Mandi_Hindi" | "Latitude" | "Longitude", ExtArgs["result"]["mandiLatLong"]>

  export type $MandiLatLongPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "MandiLatLong"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      id: number
      State: string
      Mandi: string
      Mandi_Hindi: string
      Latitude: number | null
      Longitude: number | null
    }, ExtArgs["result"]["mandiLatLong"]>
    composites: {}
  }

  type MandiLatLongGetPayload<S extends boolean | null | undefined | MandiLatLongDefaultArgs> = $Result.GetResult<Prisma.$MandiLatLongPayload, S>

  type MandiLatLongCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<MandiLatLongFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: MandiLatLongCountAggregateInputType | true
    }

  export interface MandiLatLongDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['MandiLatLong'], meta: { name: 'MandiLatLong' } }
    /**
     * Find zero or one MandiLatLong that matches the filter.
     * @param {MandiLatLongFindUniqueArgs} args - Arguments to find a MandiLatLong
     * @example
     * // Get one MandiLatLong
     * const mandiLatLong = await prisma.mandiLatLong.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends MandiLatLongFindUniqueArgs>(args: SelectSubset<T, MandiLatLongFindUniqueArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one MandiLatLong that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {MandiLatLongFindUniqueOrThrowArgs} args - Arguments to find a MandiLatLong
     * @example
     * // Get one MandiLatLong
     * const mandiLatLong = await prisma.mandiLatLong.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends MandiLatLongFindUniqueOrThrowArgs>(args: SelectSubset<T, MandiLatLongFindUniqueOrThrowArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first MandiLatLong that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongFindFirstArgs} args - Arguments to find a MandiLatLong
     * @example
     * // Get one MandiLatLong
     * const mandiLatLong = await prisma.mandiLatLong.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends MandiLatLongFindFirstArgs>(args?: SelectSubset<T, MandiLatLongFindFirstArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first MandiLatLong that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongFindFirstOrThrowArgs} args - Arguments to find a MandiLatLong
     * @example
     * // Get one MandiLatLong
     * const mandiLatLong = await prisma.mandiLatLong.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends MandiLatLongFindFirstOrThrowArgs>(args?: SelectSubset<T, MandiLatLongFindFirstOrThrowArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more MandiLatLongs that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all MandiLatLongs
     * const mandiLatLongs = await prisma.mandiLatLong.findMany()
     * 
     * // Get first 10 MandiLatLongs
     * const mandiLatLongs = await prisma.mandiLatLong.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const mandiLatLongWithIdOnly = await prisma.mandiLatLong.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends MandiLatLongFindManyArgs>(args?: SelectSubset<T, MandiLatLongFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a MandiLatLong.
     * @param {MandiLatLongCreateArgs} args - Arguments to create a MandiLatLong.
     * @example
     * // Create one MandiLatLong
     * const MandiLatLong = await prisma.mandiLatLong.create({
     *   data: {
     *     // ... data to create a MandiLatLong
     *   }
     * })
     * 
     */
    create<T extends MandiLatLongCreateArgs>(args: SelectSubset<T, MandiLatLongCreateArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many MandiLatLongs.
     * @param {MandiLatLongCreateManyArgs} args - Arguments to create many MandiLatLongs.
     * @example
     * // Create many MandiLatLongs
     * const mandiLatLong = await prisma.mandiLatLong.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends MandiLatLongCreateManyArgs>(args?: SelectSubset<T, MandiLatLongCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many MandiLatLongs and returns the data saved in the database.
     * @param {MandiLatLongCreateManyAndReturnArgs} args - Arguments to create many MandiLatLongs.
     * @example
     * // Create many MandiLatLongs
     * const mandiLatLong = await prisma.mandiLatLong.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many MandiLatLongs and only return the `id`
     * const mandiLatLongWithIdOnly = await prisma.mandiLatLong.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends MandiLatLongCreateManyAndReturnArgs>(args?: SelectSubset<T, MandiLatLongCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a MandiLatLong.
     * @param {MandiLatLongDeleteArgs} args - Arguments to delete one MandiLatLong.
     * @example
     * // Delete one MandiLatLong
     * const MandiLatLong = await prisma.mandiLatLong.delete({
     *   where: {
     *     // ... filter to delete one MandiLatLong
     *   }
     * })
     * 
     */
    delete<T extends MandiLatLongDeleteArgs>(args: SelectSubset<T, MandiLatLongDeleteArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one MandiLatLong.
     * @param {MandiLatLongUpdateArgs} args - Arguments to update one MandiLatLong.
     * @example
     * // Update one MandiLatLong
     * const mandiLatLong = await prisma.mandiLatLong.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends MandiLatLongUpdateArgs>(args: SelectSubset<T, MandiLatLongUpdateArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more MandiLatLongs.
     * @param {MandiLatLongDeleteManyArgs} args - Arguments to filter MandiLatLongs to delete.
     * @example
     * // Delete a few MandiLatLongs
     * const { count } = await prisma.mandiLatLong.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends MandiLatLongDeleteManyArgs>(args?: SelectSubset<T, MandiLatLongDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more MandiLatLongs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many MandiLatLongs
     * const mandiLatLong = await prisma.mandiLatLong.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends MandiLatLongUpdateManyArgs>(args: SelectSubset<T, MandiLatLongUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more MandiLatLongs and returns the data updated in the database.
     * @param {MandiLatLongUpdateManyAndReturnArgs} args - Arguments to update many MandiLatLongs.
     * @example
     * // Update many MandiLatLongs
     * const mandiLatLong = await prisma.mandiLatLong.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more MandiLatLongs and only return the `id`
     * const mandiLatLongWithIdOnly = await prisma.mandiLatLong.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends MandiLatLongUpdateManyAndReturnArgs>(args: SelectSubset<T, MandiLatLongUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one MandiLatLong.
     * @param {MandiLatLongUpsertArgs} args - Arguments to update or create a MandiLatLong.
     * @example
     * // Update or create a MandiLatLong
     * const mandiLatLong = await prisma.mandiLatLong.upsert({
     *   create: {
     *     // ... data to create a MandiLatLong
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the MandiLatLong we want to update
     *   }
     * })
     */
    upsert<T extends MandiLatLongUpsertArgs>(args: SelectSubset<T, MandiLatLongUpsertArgs<ExtArgs>>): Prisma__MandiLatLongClient<$Result.GetResult<Prisma.$MandiLatLongPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of MandiLatLongs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongCountArgs} args - Arguments to filter MandiLatLongs to count.
     * @example
     * // Count the number of MandiLatLongs
     * const count = await prisma.mandiLatLong.count({
     *   where: {
     *     // ... the filter for the MandiLatLongs we want to count
     *   }
     * })
    **/
    count<T extends MandiLatLongCountArgs>(
      args?: Subset<T, MandiLatLongCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], MandiLatLongCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a MandiLatLong.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends MandiLatLongAggregateArgs>(args: Subset<T, MandiLatLongAggregateArgs>): Prisma.PrismaPromise<GetMandiLatLongAggregateType<T>>

    /**
     * Group by MandiLatLong.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {MandiLatLongGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends MandiLatLongGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: MandiLatLongGroupByArgs['orderBy'] }
        : { orderBy?: MandiLatLongGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, MandiLatLongGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetMandiLatLongGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the MandiLatLong model
   */
  readonly fields: MandiLatLongFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for MandiLatLong.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__MandiLatLongClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the MandiLatLong model
   */
  interface MandiLatLongFieldRefs {
    readonly id: FieldRef<"MandiLatLong", 'Int'>
    readonly State: FieldRef<"MandiLatLong", 'String'>
    readonly Mandi: FieldRef<"MandiLatLong", 'String'>
    readonly Mandi_Hindi: FieldRef<"MandiLatLong", 'String'>
    readonly Latitude: FieldRef<"MandiLatLong", 'Float'>
    readonly Longitude: FieldRef<"MandiLatLong", 'Float'>
  }
    

  // Custom InputTypes
  /**
   * MandiLatLong findUnique
   */
  export type MandiLatLongFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * Filter, which MandiLatLong to fetch.
     */
    where: MandiLatLongWhereUniqueInput
  }

  /**
   * MandiLatLong findUniqueOrThrow
   */
  export type MandiLatLongFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * Filter, which MandiLatLong to fetch.
     */
    where: MandiLatLongWhereUniqueInput
  }

  /**
   * MandiLatLong findFirst
   */
  export type MandiLatLongFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * Filter, which MandiLatLong to fetch.
     */
    where?: MandiLatLongWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of MandiLatLongs to fetch.
     */
    orderBy?: MandiLatLongOrderByWithRelationInput | MandiLatLongOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for MandiLatLongs.
     */
    cursor?: MandiLatLongWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` MandiLatLongs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` MandiLatLongs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of MandiLatLongs.
     */
    distinct?: MandiLatLongScalarFieldEnum | MandiLatLongScalarFieldEnum[]
  }

  /**
   * MandiLatLong findFirstOrThrow
   */
  export type MandiLatLongFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * Filter, which MandiLatLong to fetch.
     */
    where?: MandiLatLongWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of MandiLatLongs to fetch.
     */
    orderBy?: MandiLatLongOrderByWithRelationInput | MandiLatLongOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for MandiLatLongs.
     */
    cursor?: MandiLatLongWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` MandiLatLongs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` MandiLatLongs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of MandiLatLongs.
     */
    distinct?: MandiLatLongScalarFieldEnum | MandiLatLongScalarFieldEnum[]
  }

  /**
   * MandiLatLong findMany
   */
  export type MandiLatLongFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * Filter, which MandiLatLongs to fetch.
     */
    where?: MandiLatLongWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of MandiLatLongs to fetch.
     */
    orderBy?: MandiLatLongOrderByWithRelationInput | MandiLatLongOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing MandiLatLongs.
     */
    cursor?: MandiLatLongWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` MandiLatLongs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` MandiLatLongs.
     */
    skip?: number
    distinct?: MandiLatLongScalarFieldEnum | MandiLatLongScalarFieldEnum[]
  }

  /**
   * MandiLatLong create
   */
  export type MandiLatLongCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * The data needed to create a MandiLatLong.
     */
    data: XOR<MandiLatLongCreateInput, MandiLatLongUncheckedCreateInput>
  }

  /**
   * MandiLatLong createMany
   */
  export type MandiLatLongCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many MandiLatLongs.
     */
    data: MandiLatLongCreateManyInput | MandiLatLongCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * MandiLatLong createManyAndReturn
   */
  export type MandiLatLongCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * The data used to create many MandiLatLongs.
     */
    data: MandiLatLongCreateManyInput | MandiLatLongCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * MandiLatLong update
   */
  export type MandiLatLongUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * The data needed to update a MandiLatLong.
     */
    data: XOR<MandiLatLongUpdateInput, MandiLatLongUncheckedUpdateInput>
    /**
     * Choose, which MandiLatLong to update.
     */
    where: MandiLatLongWhereUniqueInput
  }

  /**
   * MandiLatLong updateMany
   */
  export type MandiLatLongUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update MandiLatLongs.
     */
    data: XOR<MandiLatLongUpdateManyMutationInput, MandiLatLongUncheckedUpdateManyInput>
    /**
     * Filter which MandiLatLongs to update
     */
    where?: MandiLatLongWhereInput
    /**
     * Limit how many MandiLatLongs to update.
     */
    limit?: number
  }

  /**
   * MandiLatLong updateManyAndReturn
   */
  export type MandiLatLongUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * The data used to update MandiLatLongs.
     */
    data: XOR<MandiLatLongUpdateManyMutationInput, MandiLatLongUncheckedUpdateManyInput>
    /**
     * Filter which MandiLatLongs to update
     */
    where?: MandiLatLongWhereInput
    /**
     * Limit how many MandiLatLongs to update.
     */
    limit?: number
  }

  /**
   * MandiLatLong upsert
   */
  export type MandiLatLongUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * The filter to search for the MandiLatLong to update in case it exists.
     */
    where: MandiLatLongWhereUniqueInput
    /**
     * In case the MandiLatLong found by the `where` argument doesn't exist, create a new MandiLatLong with this data.
     */
    create: XOR<MandiLatLongCreateInput, MandiLatLongUncheckedCreateInput>
    /**
     * In case the MandiLatLong was found with the provided `where` argument, update it with this data.
     */
    update: XOR<MandiLatLongUpdateInput, MandiLatLongUncheckedUpdateInput>
  }

  /**
   * MandiLatLong delete
   */
  export type MandiLatLongDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
    /**
     * Filter which MandiLatLong to delete.
     */
    where: MandiLatLongWhereUniqueInput
  }

  /**
   * MandiLatLong deleteMany
   */
  export type MandiLatLongDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which MandiLatLongs to delete
     */
    where?: MandiLatLongWhereInput
    /**
     * Limit how many MandiLatLongs to delete.
     */
    limit?: number
  }

  /**
   * MandiLatLong without action
   */
  export type MandiLatLongDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the MandiLatLong
     */
    select?: MandiLatLongSelect<ExtArgs> | null
    /**
     * Omit specific fields from the MandiLatLong
     */
    omit?: MandiLatLongOmit<ExtArgs> | null
  }


  /**
   * Model Truck
   */

  export type AggregateTruck = {
    _count: TruckCountAggregateOutputType | null
    _avg: TruckAvgAggregateOutputType | null
    _sum: TruckSumAggregateOutputType | null
    _min: TruckMinAggregateOutputType | null
    _max: TruckMaxAggregateOutputType | null
  }

  export type TruckAvgAggregateOutputType = {
    id: number | null
    Latitude: number | null
    Longitude: number | null
  }

  export type TruckSumAggregateOutputType = {
    id: number | null
    Latitude: number | null
    Longitude: number | null
  }

  export type TruckMinAggregateOutputType = {
    id: number | null
    State: string | null
    TruckDriverName: string | null
    TruckDriverName_Hindi: string | null
    TruckNumberPlate: string | null
    Latitude: number | null
    Longitude: number | null
  }

  export type TruckMaxAggregateOutputType = {
    id: number | null
    State: string | null
    TruckDriverName: string | null
    TruckDriverName_Hindi: string | null
    TruckNumberPlate: string | null
    Latitude: number | null
    Longitude: number | null
  }

  export type TruckCountAggregateOutputType = {
    id: number
    State: number
    TruckDriverName: number
    TruckDriverName_Hindi: number
    TruckNumberPlate: number
    Latitude: number
    Longitude: number
    _all: number
  }


  export type TruckAvgAggregateInputType = {
    id?: true
    Latitude?: true
    Longitude?: true
  }

  export type TruckSumAggregateInputType = {
    id?: true
    Latitude?: true
    Longitude?: true
  }

  export type TruckMinAggregateInputType = {
    id?: true
    State?: true
    TruckDriverName?: true
    TruckDriverName_Hindi?: true
    TruckNumberPlate?: true
    Latitude?: true
    Longitude?: true
  }

  export type TruckMaxAggregateInputType = {
    id?: true
    State?: true
    TruckDriverName?: true
    TruckDriverName_Hindi?: true
    TruckNumberPlate?: true
    Latitude?: true
    Longitude?: true
  }

  export type TruckCountAggregateInputType = {
    id?: true
    State?: true
    TruckDriverName?: true
    TruckDriverName_Hindi?: true
    TruckNumberPlate?: true
    Latitude?: true
    Longitude?: true
    _all?: true
  }

  export type TruckAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Truck to aggregate.
     */
    where?: TruckWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Trucks to fetch.
     */
    orderBy?: TruckOrderByWithRelationInput | TruckOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: TruckWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Trucks from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Trucks.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Trucks
    **/
    _count?: true | TruckCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: TruckAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: TruckSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: TruckMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: TruckMaxAggregateInputType
  }

  export type GetTruckAggregateType<T extends TruckAggregateArgs> = {
        [P in keyof T & keyof AggregateTruck]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateTruck[P]>
      : GetScalarType<T[P], AggregateTruck[P]>
  }




  export type TruckGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: TruckWhereInput
    orderBy?: TruckOrderByWithAggregationInput | TruckOrderByWithAggregationInput[]
    by: TruckScalarFieldEnum[] | TruckScalarFieldEnum
    having?: TruckScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: TruckCountAggregateInputType | true
    _avg?: TruckAvgAggregateInputType
    _sum?: TruckSumAggregateInputType
    _min?: TruckMinAggregateInputType
    _max?: TruckMaxAggregateInputType
  }

  export type TruckGroupByOutputType = {
    id: number
    State: string
    TruckDriverName: string
    TruckDriverName_Hindi: string
    TruckNumberPlate: string
    Latitude: number | null
    Longitude: number | null
    _count: TruckCountAggregateOutputType | null
    _avg: TruckAvgAggregateOutputType | null
    _sum: TruckSumAggregateOutputType | null
    _min: TruckMinAggregateOutputType | null
    _max: TruckMaxAggregateOutputType | null
  }

  type GetTruckGroupByPayload<T extends TruckGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<TruckGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof TruckGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], TruckGroupByOutputType[P]>
            : GetScalarType<T[P], TruckGroupByOutputType[P]>
        }
      >
    >


  export type TruckSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    State?: boolean
    TruckDriverName?: boolean
    TruckDriverName_Hindi?: boolean
    TruckNumberPlate?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }, ExtArgs["result"]["truck"]>

  export type TruckSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    State?: boolean
    TruckDriverName?: boolean
    TruckDriverName_Hindi?: boolean
    TruckNumberPlate?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }, ExtArgs["result"]["truck"]>

  export type TruckSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    State?: boolean
    TruckDriverName?: boolean
    TruckDriverName_Hindi?: boolean
    TruckNumberPlate?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }, ExtArgs["result"]["truck"]>

  export type TruckSelectScalar = {
    id?: boolean
    State?: boolean
    TruckDriverName?: boolean
    TruckDriverName_Hindi?: boolean
    TruckNumberPlate?: boolean
    Latitude?: boolean
    Longitude?: boolean
  }

  export type TruckOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "State" | "TruckDriverName" | "TruckDriverName_Hindi" | "TruckNumberPlate" | "Latitude" | "Longitude", ExtArgs["result"]["truck"]>

  export type $TruckPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "Truck"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      id: number
      State: string
      TruckDriverName: string
      TruckDriverName_Hindi: string
      TruckNumberPlate: string
      Latitude: number | null
      Longitude: number | null
    }, ExtArgs["result"]["truck"]>
    composites: {}
  }

  type TruckGetPayload<S extends boolean | null | undefined | TruckDefaultArgs> = $Result.GetResult<Prisma.$TruckPayload, S>

  type TruckCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<TruckFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: TruckCountAggregateInputType | true
    }

  export interface TruckDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['Truck'], meta: { name: 'Truck' } }
    /**
     * Find zero or one Truck that matches the filter.
     * @param {TruckFindUniqueArgs} args - Arguments to find a Truck
     * @example
     * // Get one Truck
     * const truck = await prisma.truck.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends TruckFindUniqueArgs>(args: SelectSubset<T, TruckFindUniqueArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one Truck that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {TruckFindUniqueOrThrowArgs} args - Arguments to find a Truck
     * @example
     * // Get one Truck
     * const truck = await prisma.truck.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends TruckFindUniqueOrThrowArgs>(args: SelectSubset<T, TruckFindUniqueOrThrowArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Truck that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckFindFirstArgs} args - Arguments to find a Truck
     * @example
     * // Get one Truck
     * const truck = await prisma.truck.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends TruckFindFirstArgs>(args?: SelectSubset<T, TruckFindFirstArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Truck that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckFindFirstOrThrowArgs} args - Arguments to find a Truck
     * @example
     * // Get one Truck
     * const truck = await prisma.truck.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends TruckFindFirstOrThrowArgs>(args?: SelectSubset<T, TruckFindFirstOrThrowArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Trucks that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Trucks
     * const trucks = await prisma.truck.findMany()
     * 
     * // Get first 10 Trucks
     * const trucks = await prisma.truck.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const truckWithIdOnly = await prisma.truck.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends TruckFindManyArgs>(args?: SelectSubset<T, TruckFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a Truck.
     * @param {TruckCreateArgs} args - Arguments to create a Truck.
     * @example
     * // Create one Truck
     * const Truck = await prisma.truck.create({
     *   data: {
     *     // ... data to create a Truck
     *   }
     * })
     * 
     */
    create<T extends TruckCreateArgs>(args: SelectSubset<T, TruckCreateArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Trucks.
     * @param {TruckCreateManyArgs} args - Arguments to create many Trucks.
     * @example
     * // Create many Trucks
     * const truck = await prisma.truck.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends TruckCreateManyArgs>(args?: SelectSubset<T, TruckCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Trucks and returns the data saved in the database.
     * @param {TruckCreateManyAndReturnArgs} args - Arguments to create many Trucks.
     * @example
     * // Create many Trucks
     * const truck = await prisma.truck.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Trucks and only return the `id`
     * const truckWithIdOnly = await prisma.truck.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends TruckCreateManyAndReturnArgs>(args?: SelectSubset<T, TruckCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a Truck.
     * @param {TruckDeleteArgs} args - Arguments to delete one Truck.
     * @example
     * // Delete one Truck
     * const Truck = await prisma.truck.delete({
     *   where: {
     *     // ... filter to delete one Truck
     *   }
     * })
     * 
     */
    delete<T extends TruckDeleteArgs>(args: SelectSubset<T, TruckDeleteArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one Truck.
     * @param {TruckUpdateArgs} args - Arguments to update one Truck.
     * @example
     * // Update one Truck
     * const truck = await prisma.truck.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends TruckUpdateArgs>(args: SelectSubset<T, TruckUpdateArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Trucks.
     * @param {TruckDeleteManyArgs} args - Arguments to filter Trucks to delete.
     * @example
     * // Delete a few Trucks
     * const { count } = await prisma.truck.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends TruckDeleteManyArgs>(args?: SelectSubset<T, TruckDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Trucks.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Trucks
     * const truck = await prisma.truck.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends TruckUpdateManyArgs>(args: SelectSubset<T, TruckUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Trucks and returns the data updated in the database.
     * @param {TruckUpdateManyAndReturnArgs} args - Arguments to update many Trucks.
     * @example
     * // Update many Trucks
     * const truck = await prisma.truck.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Trucks and only return the `id`
     * const truckWithIdOnly = await prisma.truck.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends TruckUpdateManyAndReturnArgs>(args: SelectSubset<T, TruckUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one Truck.
     * @param {TruckUpsertArgs} args - Arguments to update or create a Truck.
     * @example
     * // Update or create a Truck
     * const truck = await prisma.truck.upsert({
     *   create: {
     *     // ... data to create a Truck
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the Truck we want to update
     *   }
     * })
     */
    upsert<T extends TruckUpsertArgs>(args: SelectSubset<T, TruckUpsertArgs<ExtArgs>>): Prisma__TruckClient<$Result.GetResult<Prisma.$TruckPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Trucks.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckCountArgs} args - Arguments to filter Trucks to count.
     * @example
     * // Count the number of Trucks
     * const count = await prisma.truck.count({
     *   where: {
     *     // ... the filter for the Trucks we want to count
     *   }
     * })
    **/
    count<T extends TruckCountArgs>(
      args?: Subset<T, TruckCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], TruckCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a Truck.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends TruckAggregateArgs>(args: Subset<T, TruckAggregateArgs>): Prisma.PrismaPromise<GetTruckAggregateType<T>>

    /**
     * Group by Truck.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {TruckGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends TruckGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: TruckGroupByArgs['orderBy'] }
        : { orderBy?: TruckGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, TruckGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetTruckGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the Truck model
   */
  readonly fields: TruckFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for Truck.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__TruckClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the Truck model
   */
  interface TruckFieldRefs {
    readonly id: FieldRef<"Truck", 'Int'>
    readonly State: FieldRef<"Truck", 'String'>
    readonly TruckDriverName: FieldRef<"Truck", 'String'>
    readonly TruckDriverName_Hindi: FieldRef<"Truck", 'String'>
    readonly TruckNumberPlate: FieldRef<"Truck", 'String'>
    readonly Latitude: FieldRef<"Truck", 'Float'>
    readonly Longitude: FieldRef<"Truck", 'Float'>
  }
    

  // Custom InputTypes
  /**
   * Truck findUnique
   */
  export type TruckFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * Filter, which Truck to fetch.
     */
    where: TruckWhereUniqueInput
  }

  /**
   * Truck findUniqueOrThrow
   */
  export type TruckFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * Filter, which Truck to fetch.
     */
    where: TruckWhereUniqueInput
  }

  /**
   * Truck findFirst
   */
  export type TruckFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * Filter, which Truck to fetch.
     */
    where?: TruckWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Trucks to fetch.
     */
    orderBy?: TruckOrderByWithRelationInput | TruckOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Trucks.
     */
    cursor?: TruckWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Trucks from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Trucks.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Trucks.
     */
    distinct?: TruckScalarFieldEnum | TruckScalarFieldEnum[]
  }

  /**
   * Truck findFirstOrThrow
   */
  export type TruckFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * Filter, which Truck to fetch.
     */
    where?: TruckWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Trucks to fetch.
     */
    orderBy?: TruckOrderByWithRelationInput | TruckOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Trucks.
     */
    cursor?: TruckWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Trucks from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Trucks.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Trucks.
     */
    distinct?: TruckScalarFieldEnum | TruckScalarFieldEnum[]
  }

  /**
   * Truck findMany
   */
  export type TruckFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * Filter, which Trucks to fetch.
     */
    where?: TruckWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Trucks to fetch.
     */
    orderBy?: TruckOrderByWithRelationInput | TruckOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Trucks.
     */
    cursor?: TruckWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Trucks from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Trucks.
     */
    skip?: number
    distinct?: TruckScalarFieldEnum | TruckScalarFieldEnum[]
  }

  /**
   * Truck create
   */
  export type TruckCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * The data needed to create a Truck.
     */
    data: XOR<TruckCreateInput, TruckUncheckedCreateInput>
  }

  /**
   * Truck createMany
   */
  export type TruckCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Trucks.
     */
    data: TruckCreateManyInput | TruckCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * Truck createManyAndReturn
   */
  export type TruckCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * The data used to create many Trucks.
     */
    data: TruckCreateManyInput | TruckCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * Truck update
   */
  export type TruckUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * The data needed to update a Truck.
     */
    data: XOR<TruckUpdateInput, TruckUncheckedUpdateInput>
    /**
     * Choose, which Truck to update.
     */
    where: TruckWhereUniqueInput
  }

  /**
   * Truck updateMany
   */
  export type TruckUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Trucks.
     */
    data: XOR<TruckUpdateManyMutationInput, TruckUncheckedUpdateManyInput>
    /**
     * Filter which Trucks to update
     */
    where?: TruckWhereInput
    /**
     * Limit how many Trucks to update.
     */
    limit?: number
  }

  /**
   * Truck updateManyAndReturn
   */
  export type TruckUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * The data used to update Trucks.
     */
    data: XOR<TruckUpdateManyMutationInput, TruckUncheckedUpdateManyInput>
    /**
     * Filter which Trucks to update
     */
    where?: TruckWhereInput
    /**
     * Limit how many Trucks to update.
     */
    limit?: number
  }

  /**
   * Truck upsert
   */
  export type TruckUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * The filter to search for the Truck to update in case it exists.
     */
    where: TruckWhereUniqueInput
    /**
     * In case the Truck found by the `where` argument doesn't exist, create a new Truck with this data.
     */
    create: XOR<TruckCreateInput, TruckUncheckedCreateInput>
    /**
     * In case the Truck was found with the provided `where` argument, update it with this data.
     */
    update: XOR<TruckUpdateInput, TruckUncheckedUpdateInput>
  }

  /**
   * Truck delete
   */
  export type TruckDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
    /**
     * Filter which Truck to delete.
     */
    where: TruckWhereUniqueInput
  }

  /**
   * Truck deleteMany
   */
  export type TruckDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Trucks to delete
     */
    where?: TruckWhereInput
    /**
     * Limit how many Trucks to delete.
     */
    limit?: number
  }

  /**
   * Truck without action
   */
  export type TruckDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Truck
     */
    select?: TruckSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Truck
     */
    omit?: TruckOmit<ExtArgs> | null
  }


  /**
   * Model VoiceResponse
   */

  export type AggregateVoiceResponse = {
    _count: VoiceResponseCountAggregateOutputType | null
    _avg: VoiceResponseAvgAggregateOutputType | null
    _sum: VoiceResponseSumAggregateOutputType | null
    _min: VoiceResponseMinAggregateOutputType | null
    _max: VoiceResponseMaxAggregateOutputType | null
  }

  export type VoiceResponseAvgAggregateOutputType = {
    Latitude: number | null
    Longitude: number | null
  }

  export type VoiceResponseSumAggregateOutputType = {
    Latitude: number | null
    Longitude: number | null
  }

  export type VoiceResponseMinAggregateOutputType = {
    id: string | null
    crop: string | null
    market: string | null
    quantity: string | null
    Latitude: number | null
    Longitude: number | null
    createdAt: Date | null
  }

  export type VoiceResponseMaxAggregateOutputType = {
    id: string | null
    crop: string | null
    market: string | null
    quantity: string | null
    Latitude: number | null
    Longitude: number | null
    createdAt: Date | null
  }

  export type VoiceResponseCountAggregateOutputType = {
    id: number
    crop: number
    market: number
    quantity: number
    Latitude: number
    Longitude: number
    createdAt: number
    _all: number
  }


  export type VoiceResponseAvgAggregateInputType = {
    Latitude?: true
    Longitude?: true
  }

  export type VoiceResponseSumAggregateInputType = {
    Latitude?: true
    Longitude?: true
  }

  export type VoiceResponseMinAggregateInputType = {
    id?: true
    crop?: true
    market?: true
    quantity?: true
    Latitude?: true
    Longitude?: true
    createdAt?: true
  }

  export type VoiceResponseMaxAggregateInputType = {
    id?: true
    crop?: true
    market?: true
    quantity?: true
    Latitude?: true
    Longitude?: true
    createdAt?: true
  }

  export type VoiceResponseCountAggregateInputType = {
    id?: true
    crop?: true
    market?: true
    quantity?: true
    Latitude?: true
    Longitude?: true
    createdAt?: true
    _all?: true
  }

  export type VoiceResponseAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which VoiceResponse to aggregate.
     */
    where?: VoiceResponseWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VoiceResponses to fetch.
     */
    orderBy?: VoiceResponseOrderByWithRelationInput | VoiceResponseOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: VoiceResponseWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VoiceResponses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VoiceResponses.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned VoiceResponses
    **/
    _count?: true | VoiceResponseCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: VoiceResponseAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: VoiceResponseSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: VoiceResponseMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: VoiceResponseMaxAggregateInputType
  }

  export type GetVoiceResponseAggregateType<T extends VoiceResponseAggregateArgs> = {
        [P in keyof T & keyof AggregateVoiceResponse]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateVoiceResponse[P]>
      : GetScalarType<T[P], AggregateVoiceResponse[P]>
  }




  export type VoiceResponseGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: VoiceResponseWhereInput
    orderBy?: VoiceResponseOrderByWithAggregationInput | VoiceResponseOrderByWithAggregationInput[]
    by: VoiceResponseScalarFieldEnum[] | VoiceResponseScalarFieldEnum
    having?: VoiceResponseScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: VoiceResponseCountAggregateInputType | true
    _avg?: VoiceResponseAvgAggregateInputType
    _sum?: VoiceResponseSumAggregateInputType
    _min?: VoiceResponseMinAggregateInputType
    _max?: VoiceResponseMaxAggregateInputType
  }

  export type VoiceResponseGroupByOutputType = {
    id: string
    crop: string
    market: string
    quantity: string
    Latitude: number | null
    Longitude: number | null
    createdAt: Date
    _count: VoiceResponseCountAggregateOutputType | null
    _avg: VoiceResponseAvgAggregateOutputType | null
    _sum: VoiceResponseSumAggregateOutputType | null
    _min: VoiceResponseMinAggregateOutputType | null
    _max: VoiceResponseMaxAggregateOutputType | null
  }

  type GetVoiceResponseGroupByPayload<T extends VoiceResponseGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<VoiceResponseGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof VoiceResponseGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], VoiceResponseGroupByOutputType[P]>
            : GetScalarType<T[P], VoiceResponseGroupByOutputType[P]>
        }
      >
    >


  export type VoiceResponseSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    crop?: boolean
    market?: boolean
    quantity?: boolean
    Latitude?: boolean
    Longitude?: boolean
    createdAt?: boolean
  }, ExtArgs["result"]["voiceResponse"]>

  export type VoiceResponseSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    crop?: boolean
    market?: boolean
    quantity?: boolean
    Latitude?: boolean
    Longitude?: boolean
    createdAt?: boolean
  }, ExtArgs["result"]["voiceResponse"]>

  export type VoiceResponseSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    crop?: boolean
    market?: boolean
    quantity?: boolean
    Latitude?: boolean
    Longitude?: boolean
    createdAt?: boolean
  }, ExtArgs["result"]["voiceResponse"]>

  export type VoiceResponseSelectScalar = {
    id?: boolean
    crop?: boolean
    market?: boolean
    quantity?: boolean
    Latitude?: boolean
    Longitude?: boolean
    createdAt?: boolean
  }

  export type VoiceResponseOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "crop" | "market" | "quantity" | "Latitude" | "Longitude" | "createdAt", ExtArgs["result"]["voiceResponse"]>

  export type $VoiceResponsePayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "VoiceResponse"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      id: string
      crop: string
      market: string
      quantity: string
      Latitude: number | null
      Longitude: number | null
      createdAt: Date
    }, ExtArgs["result"]["voiceResponse"]>
    composites: {}
  }

  type VoiceResponseGetPayload<S extends boolean | null | undefined | VoiceResponseDefaultArgs> = $Result.GetResult<Prisma.$VoiceResponsePayload, S>

  type VoiceResponseCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<VoiceResponseFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: VoiceResponseCountAggregateInputType | true
    }

  export interface VoiceResponseDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['VoiceResponse'], meta: { name: 'VoiceResponse' } }
    /**
     * Find zero or one VoiceResponse that matches the filter.
     * @param {VoiceResponseFindUniqueArgs} args - Arguments to find a VoiceResponse
     * @example
     * // Get one VoiceResponse
     * const voiceResponse = await prisma.voiceResponse.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends VoiceResponseFindUniqueArgs>(args: SelectSubset<T, VoiceResponseFindUniqueArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one VoiceResponse that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {VoiceResponseFindUniqueOrThrowArgs} args - Arguments to find a VoiceResponse
     * @example
     * // Get one VoiceResponse
     * const voiceResponse = await prisma.voiceResponse.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends VoiceResponseFindUniqueOrThrowArgs>(args: SelectSubset<T, VoiceResponseFindUniqueOrThrowArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first VoiceResponse that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseFindFirstArgs} args - Arguments to find a VoiceResponse
     * @example
     * // Get one VoiceResponse
     * const voiceResponse = await prisma.voiceResponse.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends VoiceResponseFindFirstArgs>(args?: SelectSubset<T, VoiceResponseFindFirstArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first VoiceResponse that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseFindFirstOrThrowArgs} args - Arguments to find a VoiceResponse
     * @example
     * // Get one VoiceResponse
     * const voiceResponse = await prisma.voiceResponse.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends VoiceResponseFindFirstOrThrowArgs>(args?: SelectSubset<T, VoiceResponseFindFirstOrThrowArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more VoiceResponses that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all VoiceResponses
     * const voiceResponses = await prisma.voiceResponse.findMany()
     * 
     * // Get first 10 VoiceResponses
     * const voiceResponses = await prisma.voiceResponse.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const voiceResponseWithIdOnly = await prisma.voiceResponse.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends VoiceResponseFindManyArgs>(args?: SelectSubset<T, VoiceResponseFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a VoiceResponse.
     * @param {VoiceResponseCreateArgs} args - Arguments to create a VoiceResponse.
     * @example
     * // Create one VoiceResponse
     * const VoiceResponse = await prisma.voiceResponse.create({
     *   data: {
     *     // ... data to create a VoiceResponse
     *   }
     * })
     * 
     */
    create<T extends VoiceResponseCreateArgs>(args: SelectSubset<T, VoiceResponseCreateArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many VoiceResponses.
     * @param {VoiceResponseCreateManyArgs} args - Arguments to create many VoiceResponses.
     * @example
     * // Create many VoiceResponses
     * const voiceResponse = await prisma.voiceResponse.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends VoiceResponseCreateManyArgs>(args?: SelectSubset<T, VoiceResponseCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many VoiceResponses and returns the data saved in the database.
     * @param {VoiceResponseCreateManyAndReturnArgs} args - Arguments to create many VoiceResponses.
     * @example
     * // Create many VoiceResponses
     * const voiceResponse = await prisma.voiceResponse.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many VoiceResponses and only return the `id`
     * const voiceResponseWithIdOnly = await prisma.voiceResponse.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends VoiceResponseCreateManyAndReturnArgs>(args?: SelectSubset<T, VoiceResponseCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a VoiceResponse.
     * @param {VoiceResponseDeleteArgs} args - Arguments to delete one VoiceResponse.
     * @example
     * // Delete one VoiceResponse
     * const VoiceResponse = await prisma.voiceResponse.delete({
     *   where: {
     *     // ... filter to delete one VoiceResponse
     *   }
     * })
     * 
     */
    delete<T extends VoiceResponseDeleteArgs>(args: SelectSubset<T, VoiceResponseDeleteArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one VoiceResponse.
     * @param {VoiceResponseUpdateArgs} args - Arguments to update one VoiceResponse.
     * @example
     * // Update one VoiceResponse
     * const voiceResponse = await prisma.voiceResponse.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends VoiceResponseUpdateArgs>(args: SelectSubset<T, VoiceResponseUpdateArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more VoiceResponses.
     * @param {VoiceResponseDeleteManyArgs} args - Arguments to filter VoiceResponses to delete.
     * @example
     * // Delete a few VoiceResponses
     * const { count } = await prisma.voiceResponse.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends VoiceResponseDeleteManyArgs>(args?: SelectSubset<T, VoiceResponseDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more VoiceResponses.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many VoiceResponses
     * const voiceResponse = await prisma.voiceResponse.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends VoiceResponseUpdateManyArgs>(args: SelectSubset<T, VoiceResponseUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more VoiceResponses and returns the data updated in the database.
     * @param {VoiceResponseUpdateManyAndReturnArgs} args - Arguments to update many VoiceResponses.
     * @example
     * // Update many VoiceResponses
     * const voiceResponse = await prisma.voiceResponse.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more VoiceResponses and only return the `id`
     * const voiceResponseWithIdOnly = await prisma.voiceResponse.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends VoiceResponseUpdateManyAndReturnArgs>(args: SelectSubset<T, VoiceResponseUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one VoiceResponse.
     * @param {VoiceResponseUpsertArgs} args - Arguments to update or create a VoiceResponse.
     * @example
     * // Update or create a VoiceResponse
     * const voiceResponse = await prisma.voiceResponse.upsert({
     *   create: {
     *     // ... data to create a VoiceResponse
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the VoiceResponse we want to update
     *   }
     * })
     */
    upsert<T extends VoiceResponseUpsertArgs>(args: SelectSubset<T, VoiceResponseUpsertArgs<ExtArgs>>): Prisma__VoiceResponseClient<$Result.GetResult<Prisma.$VoiceResponsePayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of VoiceResponses.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseCountArgs} args - Arguments to filter VoiceResponses to count.
     * @example
     * // Count the number of VoiceResponses
     * const count = await prisma.voiceResponse.count({
     *   where: {
     *     // ... the filter for the VoiceResponses we want to count
     *   }
     * })
    **/
    count<T extends VoiceResponseCountArgs>(
      args?: Subset<T, VoiceResponseCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], VoiceResponseCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a VoiceResponse.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends VoiceResponseAggregateArgs>(args: Subset<T, VoiceResponseAggregateArgs>): Prisma.PrismaPromise<GetVoiceResponseAggregateType<T>>

    /**
     * Group by VoiceResponse.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VoiceResponseGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends VoiceResponseGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: VoiceResponseGroupByArgs['orderBy'] }
        : { orderBy?: VoiceResponseGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, VoiceResponseGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetVoiceResponseGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the VoiceResponse model
   */
  readonly fields: VoiceResponseFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for VoiceResponse.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__VoiceResponseClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the VoiceResponse model
   */
  interface VoiceResponseFieldRefs {
    readonly id: FieldRef<"VoiceResponse", 'String'>
    readonly crop: FieldRef<"VoiceResponse", 'String'>
    readonly market: FieldRef<"VoiceResponse", 'String'>
    readonly quantity: FieldRef<"VoiceResponse", 'String'>
    readonly Latitude: FieldRef<"VoiceResponse", 'Float'>
    readonly Longitude: FieldRef<"VoiceResponse", 'Float'>
    readonly createdAt: FieldRef<"VoiceResponse", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * VoiceResponse findUnique
   */
  export type VoiceResponseFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * Filter, which VoiceResponse to fetch.
     */
    where: VoiceResponseWhereUniqueInput
  }

  /**
   * VoiceResponse findUniqueOrThrow
   */
  export type VoiceResponseFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * Filter, which VoiceResponse to fetch.
     */
    where: VoiceResponseWhereUniqueInput
  }

  /**
   * VoiceResponse findFirst
   */
  export type VoiceResponseFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * Filter, which VoiceResponse to fetch.
     */
    where?: VoiceResponseWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VoiceResponses to fetch.
     */
    orderBy?: VoiceResponseOrderByWithRelationInput | VoiceResponseOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for VoiceResponses.
     */
    cursor?: VoiceResponseWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VoiceResponses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VoiceResponses.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of VoiceResponses.
     */
    distinct?: VoiceResponseScalarFieldEnum | VoiceResponseScalarFieldEnum[]
  }

  /**
   * VoiceResponse findFirstOrThrow
   */
  export type VoiceResponseFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * Filter, which VoiceResponse to fetch.
     */
    where?: VoiceResponseWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VoiceResponses to fetch.
     */
    orderBy?: VoiceResponseOrderByWithRelationInput | VoiceResponseOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for VoiceResponses.
     */
    cursor?: VoiceResponseWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VoiceResponses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VoiceResponses.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of VoiceResponses.
     */
    distinct?: VoiceResponseScalarFieldEnum | VoiceResponseScalarFieldEnum[]
  }

  /**
   * VoiceResponse findMany
   */
  export type VoiceResponseFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * Filter, which VoiceResponses to fetch.
     */
    where?: VoiceResponseWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VoiceResponses to fetch.
     */
    orderBy?: VoiceResponseOrderByWithRelationInput | VoiceResponseOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing VoiceResponses.
     */
    cursor?: VoiceResponseWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VoiceResponses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VoiceResponses.
     */
    skip?: number
    distinct?: VoiceResponseScalarFieldEnum | VoiceResponseScalarFieldEnum[]
  }

  /**
   * VoiceResponse create
   */
  export type VoiceResponseCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * The data needed to create a VoiceResponse.
     */
    data: XOR<VoiceResponseCreateInput, VoiceResponseUncheckedCreateInput>
  }

  /**
   * VoiceResponse createMany
   */
  export type VoiceResponseCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many VoiceResponses.
     */
    data: VoiceResponseCreateManyInput | VoiceResponseCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * VoiceResponse createManyAndReturn
   */
  export type VoiceResponseCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * The data used to create many VoiceResponses.
     */
    data: VoiceResponseCreateManyInput | VoiceResponseCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * VoiceResponse update
   */
  export type VoiceResponseUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * The data needed to update a VoiceResponse.
     */
    data: XOR<VoiceResponseUpdateInput, VoiceResponseUncheckedUpdateInput>
    /**
     * Choose, which VoiceResponse to update.
     */
    where: VoiceResponseWhereUniqueInput
  }

  /**
   * VoiceResponse updateMany
   */
  export type VoiceResponseUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update VoiceResponses.
     */
    data: XOR<VoiceResponseUpdateManyMutationInput, VoiceResponseUncheckedUpdateManyInput>
    /**
     * Filter which VoiceResponses to update
     */
    where?: VoiceResponseWhereInput
    /**
     * Limit how many VoiceResponses to update.
     */
    limit?: number
  }

  /**
   * VoiceResponse updateManyAndReturn
   */
  export type VoiceResponseUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * The data used to update VoiceResponses.
     */
    data: XOR<VoiceResponseUpdateManyMutationInput, VoiceResponseUncheckedUpdateManyInput>
    /**
     * Filter which VoiceResponses to update
     */
    where?: VoiceResponseWhereInput
    /**
     * Limit how many VoiceResponses to update.
     */
    limit?: number
  }

  /**
   * VoiceResponse upsert
   */
  export type VoiceResponseUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * The filter to search for the VoiceResponse to update in case it exists.
     */
    where: VoiceResponseWhereUniqueInput
    /**
     * In case the VoiceResponse found by the `where` argument doesn't exist, create a new VoiceResponse with this data.
     */
    create: XOR<VoiceResponseCreateInput, VoiceResponseUncheckedCreateInput>
    /**
     * In case the VoiceResponse was found with the provided `where` argument, update it with this data.
     */
    update: XOR<VoiceResponseUpdateInput, VoiceResponseUncheckedUpdateInput>
  }

  /**
   * VoiceResponse delete
   */
  export type VoiceResponseDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
    /**
     * Filter which VoiceResponse to delete.
     */
    where: VoiceResponseWhereUniqueInput
  }

  /**
   * VoiceResponse deleteMany
   */
  export type VoiceResponseDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which VoiceResponses to delete
     */
    where?: VoiceResponseWhereInput
    /**
     * Limit how many VoiceResponses to delete.
     */
    limit?: number
  }

  /**
   * VoiceResponse without action
   */
  export type VoiceResponseDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VoiceResponse
     */
    select?: VoiceResponseSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VoiceResponse
     */
    omit?: VoiceResponseOmit<ExtArgs> | null
  }


  /**
   * Enums
   */

  export const TransactionIsolationLevel: {
    ReadUncommitted: 'ReadUncommitted',
    ReadCommitted: 'ReadCommitted',
    RepeatableRead: 'RepeatableRead',
    Serializable: 'Serializable'
  };

  export type TransactionIsolationLevel = (typeof TransactionIsolationLevel)[keyof typeof TransactionIsolationLevel]


  export const UserScalarFieldEnum: {
    id: 'id',
    email: 'email',
    firstName: 'firstName',
    lastName: 'lastName',
    profileImage: 'profileImage',
    createdAt: 'createdAt'
  };

  export type UserScalarFieldEnum = (typeof UserScalarFieldEnum)[keyof typeof UserScalarFieldEnum]


  export const MandiLatLongScalarFieldEnum: {
    id: 'id',
    State: 'State',
    Mandi: 'Mandi',
    Mandi_Hindi: 'Mandi_Hindi',
    Latitude: 'Latitude',
    Longitude: 'Longitude'
  };

  export type MandiLatLongScalarFieldEnum = (typeof MandiLatLongScalarFieldEnum)[keyof typeof MandiLatLongScalarFieldEnum]


  export const TruckScalarFieldEnum: {
    id: 'id',
    State: 'State',
    TruckDriverName: 'TruckDriverName',
    TruckDriverName_Hindi: 'TruckDriverName_Hindi',
    TruckNumberPlate: 'TruckNumberPlate',
    Latitude: 'Latitude',
    Longitude: 'Longitude'
  };

  export type TruckScalarFieldEnum = (typeof TruckScalarFieldEnum)[keyof typeof TruckScalarFieldEnum]


  export const VoiceResponseScalarFieldEnum: {
    id: 'id',
    crop: 'crop',
    market: 'market',
    quantity: 'quantity',
    Latitude: 'Latitude',
    Longitude: 'Longitude',
    createdAt: 'createdAt'
  };

  export type VoiceResponseScalarFieldEnum = (typeof VoiceResponseScalarFieldEnum)[keyof typeof VoiceResponseScalarFieldEnum]


  export const SortOrder: {
    asc: 'asc',
    desc: 'desc'
  };

  export type SortOrder = (typeof SortOrder)[keyof typeof SortOrder]


  export const QueryMode: {
    default: 'default',
    insensitive: 'insensitive'
  };

  export type QueryMode = (typeof QueryMode)[keyof typeof QueryMode]


  export const NullsOrder: {
    first: 'first',
    last: 'last'
  };

  export type NullsOrder = (typeof NullsOrder)[keyof typeof NullsOrder]


  /**
   * Field references
   */


  /**
   * Reference to a field of type 'String'
   */
  export type StringFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'String'>
    


  /**
   * Reference to a field of type 'String[]'
   */
  export type ListStringFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'String[]'>
    


  /**
   * Reference to a field of type 'DateTime'
   */
  export type DateTimeFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'DateTime'>
    


  /**
   * Reference to a field of type 'DateTime[]'
   */
  export type ListDateTimeFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'DateTime[]'>
    


  /**
   * Reference to a field of type 'Int'
   */
  export type IntFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Int'>
    


  /**
   * Reference to a field of type 'Int[]'
   */
  export type ListIntFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Int[]'>
    


  /**
   * Reference to a field of type 'Float'
   */
  export type FloatFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Float'>
    


  /**
   * Reference to a field of type 'Float[]'
   */
  export type ListFloatFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Float[]'>
    
  /**
   * Deep Input Types
   */


  export type UserWhereInput = {
    AND?: UserWhereInput | UserWhereInput[]
    OR?: UserWhereInput[]
    NOT?: UserWhereInput | UserWhereInput[]
    id?: StringFilter<"User"> | string
    email?: StringFilter<"User"> | string
    firstName?: StringFilter<"User"> | string
    lastName?: StringFilter<"User"> | string
    profileImage?: StringFilter<"User"> | string
    createdAt?: DateTimeFilter<"User"> | Date | string
  }

  export type UserOrderByWithRelationInput = {
    id?: SortOrder
    email?: SortOrder
    firstName?: SortOrder
    lastName?: SortOrder
    profileImage?: SortOrder
    createdAt?: SortOrder
  }

  export type UserWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    email?: string
    AND?: UserWhereInput | UserWhereInput[]
    OR?: UserWhereInput[]
    NOT?: UserWhereInput | UserWhereInput[]
    firstName?: StringFilter<"User"> | string
    lastName?: StringFilter<"User"> | string
    profileImage?: StringFilter<"User"> | string
    createdAt?: DateTimeFilter<"User"> | Date | string
  }, "id" | "id" | "email">

  export type UserOrderByWithAggregationInput = {
    id?: SortOrder
    email?: SortOrder
    firstName?: SortOrder
    lastName?: SortOrder
    profileImage?: SortOrder
    createdAt?: SortOrder
    _count?: UserCountOrderByAggregateInput
    _max?: UserMaxOrderByAggregateInput
    _min?: UserMinOrderByAggregateInput
  }

  export type UserScalarWhereWithAggregatesInput = {
    AND?: UserScalarWhereWithAggregatesInput | UserScalarWhereWithAggregatesInput[]
    OR?: UserScalarWhereWithAggregatesInput[]
    NOT?: UserScalarWhereWithAggregatesInput | UserScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"User"> | string
    email?: StringWithAggregatesFilter<"User"> | string
    firstName?: StringWithAggregatesFilter<"User"> | string
    lastName?: StringWithAggregatesFilter<"User"> | string
    profileImage?: StringWithAggregatesFilter<"User"> | string
    createdAt?: DateTimeWithAggregatesFilter<"User"> | Date | string
  }

  export type MandiLatLongWhereInput = {
    AND?: MandiLatLongWhereInput | MandiLatLongWhereInput[]
    OR?: MandiLatLongWhereInput[]
    NOT?: MandiLatLongWhereInput | MandiLatLongWhereInput[]
    id?: IntFilter<"MandiLatLong"> | number
    State?: StringFilter<"MandiLatLong"> | string
    Mandi?: StringFilter<"MandiLatLong"> | string
    Mandi_Hindi?: StringFilter<"MandiLatLong"> | string
    Latitude?: FloatNullableFilter<"MandiLatLong"> | number | null
    Longitude?: FloatNullableFilter<"MandiLatLong"> | number | null
  }

  export type MandiLatLongOrderByWithRelationInput = {
    id?: SortOrder
    State?: SortOrder
    Mandi?: SortOrder
    Mandi_Hindi?: SortOrder
    Latitude?: SortOrderInput | SortOrder
    Longitude?: SortOrderInput | SortOrder
  }

  export type MandiLatLongWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: MandiLatLongWhereInput | MandiLatLongWhereInput[]
    OR?: MandiLatLongWhereInput[]
    NOT?: MandiLatLongWhereInput | MandiLatLongWhereInput[]
    State?: StringFilter<"MandiLatLong"> | string
    Mandi?: StringFilter<"MandiLatLong"> | string
    Mandi_Hindi?: StringFilter<"MandiLatLong"> | string
    Latitude?: FloatNullableFilter<"MandiLatLong"> | number | null
    Longitude?: FloatNullableFilter<"MandiLatLong"> | number | null
  }, "id">

  export type MandiLatLongOrderByWithAggregationInput = {
    id?: SortOrder
    State?: SortOrder
    Mandi?: SortOrder
    Mandi_Hindi?: SortOrder
    Latitude?: SortOrderInput | SortOrder
    Longitude?: SortOrderInput | SortOrder
    _count?: MandiLatLongCountOrderByAggregateInput
    _avg?: MandiLatLongAvgOrderByAggregateInput
    _max?: MandiLatLongMaxOrderByAggregateInput
    _min?: MandiLatLongMinOrderByAggregateInput
    _sum?: MandiLatLongSumOrderByAggregateInput
  }

  export type MandiLatLongScalarWhereWithAggregatesInput = {
    AND?: MandiLatLongScalarWhereWithAggregatesInput | MandiLatLongScalarWhereWithAggregatesInput[]
    OR?: MandiLatLongScalarWhereWithAggregatesInput[]
    NOT?: MandiLatLongScalarWhereWithAggregatesInput | MandiLatLongScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"MandiLatLong"> | number
    State?: StringWithAggregatesFilter<"MandiLatLong"> | string
    Mandi?: StringWithAggregatesFilter<"MandiLatLong"> | string
    Mandi_Hindi?: StringWithAggregatesFilter<"MandiLatLong"> | string
    Latitude?: FloatNullableWithAggregatesFilter<"MandiLatLong"> | number | null
    Longitude?: FloatNullableWithAggregatesFilter<"MandiLatLong"> | number | null
  }

  export type TruckWhereInput = {
    AND?: TruckWhereInput | TruckWhereInput[]
    OR?: TruckWhereInput[]
    NOT?: TruckWhereInput | TruckWhereInput[]
    id?: IntFilter<"Truck"> | number
    State?: StringFilter<"Truck"> | string
    TruckDriverName?: StringFilter<"Truck"> | string
    TruckDriverName_Hindi?: StringFilter<"Truck"> | string
    TruckNumberPlate?: StringFilter<"Truck"> | string
    Latitude?: FloatNullableFilter<"Truck"> | number | null
    Longitude?: FloatNullableFilter<"Truck"> | number | null
  }

  export type TruckOrderByWithRelationInput = {
    id?: SortOrder
    State?: SortOrder
    TruckDriverName?: SortOrder
    TruckDriverName_Hindi?: SortOrder
    TruckNumberPlate?: SortOrder
    Latitude?: SortOrderInput | SortOrder
    Longitude?: SortOrderInput | SortOrder
  }

  export type TruckWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    TruckNumberPlate?: string
    AND?: TruckWhereInput | TruckWhereInput[]
    OR?: TruckWhereInput[]
    NOT?: TruckWhereInput | TruckWhereInput[]
    State?: StringFilter<"Truck"> | string
    TruckDriverName?: StringFilter<"Truck"> | string
    TruckDriverName_Hindi?: StringFilter<"Truck"> | string
    Latitude?: FloatNullableFilter<"Truck"> | number | null
    Longitude?: FloatNullableFilter<"Truck"> | number | null
  }, "id" | "TruckNumberPlate">

  export type TruckOrderByWithAggregationInput = {
    id?: SortOrder
    State?: SortOrder
    TruckDriverName?: SortOrder
    TruckDriverName_Hindi?: SortOrder
    TruckNumberPlate?: SortOrder
    Latitude?: SortOrderInput | SortOrder
    Longitude?: SortOrderInput | SortOrder
    _count?: TruckCountOrderByAggregateInput
    _avg?: TruckAvgOrderByAggregateInput
    _max?: TruckMaxOrderByAggregateInput
    _min?: TruckMinOrderByAggregateInput
    _sum?: TruckSumOrderByAggregateInput
  }

  export type TruckScalarWhereWithAggregatesInput = {
    AND?: TruckScalarWhereWithAggregatesInput | TruckScalarWhereWithAggregatesInput[]
    OR?: TruckScalarWhereWithAggregatesInput[]
    NOT?: TruckScalarWhereWithAggregatesInput | TruckScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"Truck"> | number
    State?: StringWithAggregatesFilter<"Truck"> | string
    TruckDriverName?: StringWithAggregatesFilter<"Truck"> | string
    TruckDriverName_Hindi?: StringWithAggregatesFilter<"Truck"> | string
    TruckNumberPlate?: StringWithAggregatesFilter<"Truck"> | string
    Latitude?: FloatNullableWithAggregatesFilter<"Truck"> | number | null
    Longitude?: FloatNullableWithAggregatesFilter<"Truck"> | number | null
  }

  export type VoiceResponseWhereInput = {
    AND?: VoiceResponseWhereInput | VoiceResponseWhereInput[]
    OR?: VoiceResponseWhereInput[]
    NOT?: VoiceResponseWhereInput | VoiceResponseWhereInput[]
    id?: StringFilter<"VoiceResponse"> | string
    crop?: StringFilter<"VoiceResponse"> | string
    market?: StringFilter<"VoiceResponse"> | string
    quantity?: StringFilter<"VoiceResponse"> | string
    Latitude?: FloatNullableFilter<"VoiceResponse"> | number | null
    Longitude?: FloatNullableFilter<"VoiceResponse"> | number | null
    createdAt?: DateTimeFilter<"VoiceResponse"> | Date | string
  }

  export type VoiceResponseOrderByWithRelationInput = {
    id?: SortOrder
    crop?: SortOrder
    market?: SortOrder
    quantity?: SortOrder
    Latitude?: SortOrderInput | SortOrder
    Longitude?: SortOrderInput | SortOrder
    createdAt?: SortOrder
  }

  export type VoiceResponseWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    AND?: VoiceResponseWhereInput | VoiceResponseWhereInput[]
    OR?: VoiceResponseWhereInput[]
    NOT?: VoiceResponseWhereInput | VoiceResponseWhereInput[]
    crop?: StringFilter<"VoiceResponse"> | string
    market?: StringFilter<"VoiceResponse"> | string
    quantity?: StringFilter<"VoiceResponse"> | string
    Latitude?: FloatNullableFilter<"VoiceResponse"> | number | null
    Longitude?: FloatNullableFilter<"VoiceResponse"> | number | null
    createdAt?: DateTimeFilter<"VoiceResponse"> | Date | string
  }, "id">

  export type VoiceResponseOrderByWithAggregationInput = {
    id?: SortOrder
    crop?: SortOrder
    market?: SortOrder
    quantity?: SortOrder
    Latitude?: SortOrderInput | SortOrder
    Longitude?: SortOrderInput | SortOrder
    createdAt?: SortOrder
    _count?: VoiceResponseCountOrderByAggregateInput
    _avg?: VoiceResponseAvgOrderByAggregateInput
    _max?: VoiceResponseMaxOrderByAggregateInput
    _min?: VoiceResponseMinOrderByAggregateInput
    _sum?: VoiceResponseSumOrderByAggregateInput
  }

  export type VoiceResponseScalarWhereWithAggregatesInput = {
    AND?: VoiceResponseScalarWhereWithAggregatesInput | VoiceResponseScalarWhereWithAggregatesInput[]
    OR?: VoiceResponseScalarWhereWithAggregatesInput[]
    NOT?: VoiceResponseScalarWhereWithAggregatesInput | VoiceResponseScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"VoiceResponse"> | string
    crop?: StringWithAggregatesFilter<"VoiceResponse"> | string
    market?: StringWithAggregatesFilter<"VoiceResponse"> | string
    quantity?: StringWithAggregatesFilter<"VoiceResponse"> | string
    Latitude?: FloatNullableWithAggregatesFilter<"VoiceResponse"> | number | null
    Longitude?: FloatNullableWithAggregatesFilter<"VoiceResponse"> | number | null
    createdAt?: DateTimeWithAggregatesFilter<"VoiceResponse"> | Date | string
  }

  export type UserCreateInput = {
    id: string
    email: string
    firstName: string
    lastName: string
    profileImage: string
    createdAt?: Date | string
  }

  export type UserUncheckedCreateInput = {
    id: string
    email: string
    firstName: string
    lastName: string
    profileImage: string
    createdAt?: Date | string
  }

  export type UserUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    firstName?: StringFieldUpdateOperationsInput | string
    lastName?: StringFieldUpdateOperationsInput | string
    profileImage?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type UserUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    firstName?: StringFieldUpdateOperationsInput | string
    lastName?: StringFieldUpdateOperationsInput | string
    profileImage?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type UserCreateManyInput = {
    id: string
    email: string
    firstName: string
    lastName: string
    profileImage: string
    createdAt?: Date | string
  }

  export type UserUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    firstName?: StringFieldUpdateOperationsInput | string
    lastName?: StringFieldUpdateOperationsInput | string
    profileImage?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type UserUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    firstName?: StringFieldUpdateOperationsInput | string
    lastName?: StringFieldUpdateOperationsInput | string
    profileImage?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type MandiLatLongCreateInput = {
    State: string
    Mandi: string
    Mandi_Hindi: string
    Latitude?: number | null
    Longitude?: number | null
  }

  export type MandiLatLongUncheckedCreateInput = {
    id?: number
    State: string
    Mandi: string
    Mandi_Hindi: string
    Latitude?: number | null
    Longitude?: number | null
  }

  export type MandiLatLongUpdateInput = {
    State?: StringFieldUpdateOperationsInput | string
    Mandi?: StringFieldUpdateOperationsInput | string
    Mandi_Hindi?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type MandiLatLongUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    State?: StringFieldUpdateOperationsInput | string
    Mandi?: StringFieldUpdateOperationsInput | string
    Mandi_Hindi?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type MandiLatLongCreateManyInput = {
    id?: number
    State: string
    Mandi: string
    Mandi_Hindi: string
    Latitude?: number | null
    Longitude?: number | null
  }

  export type MandiLatLongUpdateManyMutationInput = {
    State?: StringFieldUpdateOperationsInput | string
    Mandi?: StringFieldUpdateOperationsInput | string
    Mandi_Hindi?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type MandiLatLongUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    State?: StringFieldUpdateOperationsInput | string
    Mandi?: StringFieldUpdateOperationsInput | string
    Mandi_Hindi?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type TruckCreateInput = {
    State: string
    TruckDriverName: string
    TruckDriverName_Hindi: string
    TruckNumberPlate: string
    Latitude?: number | null
    Longitude?: number | null
  }

  export type TruckUncheckedCreateInput = {
    id?: number
    State: string
    TruckDriverName: string
    TruckDriverName_Hindi: string
    TruckNumberPlate: string
    Latitude?: number | null
    Longitude?: number | null
  }

  export type TruckUpdateInput = {
    State?: StringFieldUpdateOperationsInput | string
    TruckDriverName?: StringFieldUpdateOperationsInput | string
    TruckDriverName_Hindi?: StringFieldUpdateOperationsInput | string
    TruckNumberPlate?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type TruckUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    State?: StringFieldUpdateOperationsInput | string
    TruckDriverName?: StringFieldUpdateOperationsInput | string
    TruckDriverName_Hindi?: StringFieldUpdateOperationsInput | string
    TruckNumberPlate?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type TruckCreateManyInput = {
    id?: number
    State: string
    TruckDriverName: string
    TruckDriverName_Hindi: string
    TruckNumberPlate: string
    Latitude?: number | null
    Longitude?: number | null
  }

  export type TruckUpdateManyMutationInput = {
    State?: StringFieldUpdateOperationsInput | string
    TruckDriverName?: StringFieldUpdateOperationsInput | string
    TruckDriverName_Hindi?: StringFieldUpdateOperationsInput | string
    TruckNumberPlate?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type TruckUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    State?: StringFieldUpdateOperationsInput | string
    TruckDriverName?: StringFieldUpdateOperationsInput | string
    TruckDriverName_Hindi?: StringFieldUpdateOperationsInput | string
    TruckNumberPlate?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
  }

  export type VoiceResponseCreateInput = {
    id?: string
    crop: string
    market: string
    quantity: string
    Latitude?: number | null
    Longitude?: number | null
    createdAt?: Date | string
  }

  export type VoiceResponseUncheckedCreateInput = {
    id?: string
    crop: string
    market: string
    quantity: string
    Latitude?: number | null
    Longitude?: number | null
    createdAt?: Date | string
  }

  export type VoiceResponseUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    crop?: StringFieldUpdateOperationsInput | string
    market?: StringFieldUpdateOperationsInput | string
    quantity?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type VoiceResponseUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    crop?: StringFieldUpdateOperationsInput | string
    market?: StringFieldUpdateOperationsInput | string
    quantity?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type VoiceResponseCreateManyInput = {
    id?: string
    crop: string
    market: string
    quantity: string
    Latitude?: number | null
    Longitude?: number | null
    createdAt?: Date | string
  }

  export type VoiceResponseUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    crop?: StringFieldUpdateOperationsInput | string
    market?: StringFieldUpdateOperationsInput | string
    quantity?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type VoiceResponseUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    crop?: StringFieldUpdateOperationsInput | string
    market?: StringFieldUpdateOperationsInput | string
    quantity?: StringFieldUpdateOperationsInput | string
    Latitude?: NullableFloatFieldUpdateOperationsInput | number | null
    Longitude?: NullableFloatFieldUpdateOperationsInput | number | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type StringFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    mode?: QueryMode
    not?: NestedStringFilter<$PrismaModel> | string
  }

  export type DateTimeFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeFilter<$PrismaModel> | Date | string
  }

  export type UserCountOrderByAggregateInput = {
    id?: SortOrder
    email?: SortOrder
    firstName?: SortOrder
    lastName?: SortOrder
    profileImage?: SortOrder
    createdAt?: SortOrder
  }

  export type UserMaxOrderByAggregateInput = {
    id?: SortOrder
    email?: SortOrder
    firstName?: SortOrder
    lastName?: SortOrder
    profileImage?: SortOrder
    createdAt?: SortOrder
  }

  export type UserMinOrderByAggregateInput = {
    id?: SortOrder
    email?: SortOrder
    firstName?: SortOrder
    lastName?: SortOrder
    profileImage?: SortOrder
    createdAt?: SortOrder
  }

  export type StringWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    mode?: QueryMode
    not?: NestedStringWithAggregatesFilter<$PrismaModel> | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedStringFilter<$PrismaModel>
    _max?: NestedStringFilter<$PrismaModel>
  }

  export type DateTimeWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeWithAggregatesFilter<$PrismaModel> | Date | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedDateTimeFilter<$PrismaModel>
    _max?: NestedDateTimeFilter<$PrismaModel>
  }

  export type IntFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntFilter<$PrismaModel> | number
  }

  export type FloatNullableFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableFilter<$PrismaModel> | number | null
  }

  export type SortOrderInput = {
    sort: SortOrder
    nulls?: NullsOrder
  }

  export type MandiLatLongCountOrderByAggregateInput = {
    id?: SortOrder
    State?: SortOrder
    Mandi?: SortOrder
    Mandi_Hindi?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type MandiLatLongAvgOrderByAggregateInput = {
    id?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type MandiLatLongMaxOrderByAggregateInput = {
    id?: SortOrder
    State?: SortOrder
    Mandi?: SortOrder
    Mandi_Hindi?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type MandiLatLongMinOrderByAggregateInput = {
    id?: SortOrder
    State?: SortOrder
    Mandi?: SortOrder
    Mandi_Hindi?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type MandiLatLongSumOrderByAggregateInput = {
    id?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type IntWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntWithAggregatesFilter<$PrismaModel> | number
    _count?: NestedIntFilter<$PrismaModel>
    _avg?: NestedFloatFilter<$PrismaModel>
    _sum?: NestedIntFilter<$PrismaModel>
    _min?: NestedIntFilter<$PrismaModel>
    _max?: NestedIntFilter<$PrismaModel>
  }

  export type FloatNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedFloatNullableFilter<$PrismaModel>
    _min?: NestedFloatNullableFilter<$PrismaModel>
    _max?: NestedFloatNullableFilter<$PrismaModel>
  }

  export type TruckCountOrderByAggregateInput = {
    id?: SortOrder
    State?: SortOrder
    TruckDriverName?: SortOrder
    TruckDriverName_Hindi?: SortOrder
    TruckNumberPlate?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type TruckAvgOrderByAggregateInput = {
    id?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type TruckMaxOrderByAggregateInput = {
    id?: SortOrder
    State?: SortOrder
    TruckDriverName?: SortOrder
    TruckDriverName_Hindi?: SortOrder
    TruckNumberPlate?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type TruckMinOrderByAggregateInput = {
    id?: SortOrder
    State?: SortOrder
    TruckDriverName?: SortOrder
    TruckDriverName_Hindi?: SortOrder
    TruckNumberPlate?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type TruckSumOrderByAggregateInput = {
    id?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type VoiceResponseCountOrderByAggregateInput = {
    id?: SortOrder
    crop?: SortOrder
    market?: SortOrder
    quantity?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
    createdAt?: SortOrder
  }

  export type VoiceResponseAvgOrderByAggregateInput = {
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type VoiceResponseMaxOrderByAggregateInput = {
    id?: SortOrder
    crop?: SortOrder
    market?: SortOrder
    quantity?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
    createdAt?: SortOrder
  }

  export type VoiceResponseMinOrderByAggregateInput = {
    id?: SortOrder
    crop?: SortOrder
    market?: SortOrder
    quantity?: SortOrder
    Latitude?: SortOrder
    Longitude?: SortOrder
    createdAt?: SortOrder
  }

  export type VoiceResponseSumOrderByAggregateInput = {
    Latitude?: SortOrder
    Longitude?: SortOrder
  }

  export type StringFieldUpdateOperationsInput = {
    set?: string
  }

  export type DateTimeFieldUpdateOperationsInput = {
    set?: Date | string
  }

  export type NullableFloatFieldUpdateOperationsInput = {
    set?: number | null
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type IntFieldUpdateOperationsInput = {
    set?: number
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type NestedStringFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringFilter<$PrismaModel> | string
  }

  export type NestedDateTimeFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeFilter<$PrismaModel> | Date | string
  }

  export type NestedStringWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringWithAggregatesFilter<$PrismaModel> | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedStringFilter<$PrismaModel>
    _max?: NestedStringFilter<$PrismaModel>
  }

  export type NestedIntFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntFilter<$PrismaModel> | number
  }

  export type NestedDateTimeWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeWithAggregatesFilter<$PrismaModel> | Date | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedDateTimeFilter<$PrismaModel>
    _max?: NestedDateTimeFilter<$PrismaModel>
  }

  export type NestedFloatNullableFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableFilter<$PrismaModel> | number | null
  }

  export type NestedIntWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntWithAggregatesFilter<$PrismaModel> | number
    _count?: NestedIntFilter<$PrismaModel>
    _avg?: NestedFloatFilter<$PrismaModel>
    _sum?: NestedIntFilter<$PrismaModel>
    _min?: NestedIntFilter<$PrismaModel>
    _max?: NestedIntFilter<$PrismaModel>
  }

  export type NestedFloatFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel>
    in?: number[] | ListFloatFieldRefInput<$PrismaModel>
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel>
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatFilter<$PrismaModel> | number
  }

  export type NestedFloatNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedFloatNullableFilter<$PrismaModel>
    _min?: NestedFloatNullableFilter<$PrismaModel>
    _max?: NestedFloatNullableFilter<$PrismaModel>
  }

  export type NestedIntNullableFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableFilter<$PrismaModel> | number | null
  }



  /**
   * Batch Payload for updateMany & deleteMany & createMany
   */

  export type BatchPayload = {
    count: number
  }

  /**
   * DMMF
   */
  export const dmmf: runtime.BaseDMMF
}